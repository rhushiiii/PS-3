"""Transparent, rule-based integrity review prompts.

Everything here is deterministic arithmetic over stored data. Signals are prompts
for an officer to look, never fraud or compliance determinations. Counts, rule
ids and entity ids are the only evidence: no APAAR values, names or student ids.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.core.pagination import paginate_list
from app.modules.audit.services import record_action
from app.modules.auth.models import User
from app.modules.cases.models import CaseEvent, CaseRecord, ReviewCase
from app.modules.cases.services import case_flags
from app.modules.institutions.models import Institution, Programme
from app.modules.institutions.services import scoped_programme
from app.modules.intake.models import IntakeAssessment
from app.modules.intake.services import (
    active_by_category,
    capacity_line,
    configured_rules,
    intake_actor,
    latest_declaration,
    snapshot_diff,
)
from app.modules.integrity.models import IntegrityDecision
from app.modules.integrity.schemas import (
    FAMILIES,
    SEVERITIES,
    Band,
    DecisionRequest,
    EvidenceRefs,
    Family,
    FamilyScore,
    OverviewItem,
    OverviewResponse,
    ScoreSummary,
    Severity,
    Signal,
    SignalsResponse,
)
from app.modules.submissions.models import (
    ProcessingStatus,
    SubmissionBatch,
    SubmissionReview,
    SubmissionScope,
)
from app.modules.submissions.services import batch_rows
from app.modules.validation.models import ValidationFinding
from app.modules.validation.rules import CATEGORIES
from app.modules.validation.services import selected_run
from app.modules.verification.models import ApaarVerification

RECORD_ID_CAP = 20
CASE_ID_CAP = 50
SEVERITY_RANK = {severity: rank for rank, severity in enumerate(SEVERITIES)}

# validation rule codes feeding each DATA_QUALITY signal
DQ_SOURCES: dict[str, tuple[str, ...]] = {
    "DQ_MISSING_FIELDS": ("REQUIRED_FIELD_MISSING",),
    "DQ_MALFORMED_APAAR": ("INVALID_APAAR_FORMAT",),
    "DQ_DUPLICATE_IDENTIFIERS": ("DUPLICATE_COLLEGE_STUDENT_ID", "DUPLICATE_IN_BATCH"),
}
CROSS_INSTITUTION_CODE = "POTENTIAL_CROSS_INSTITUTION_DUPLICATE"
VERIFICATION_SEVERITY: dict[str, Severity] = {
    "PENDING": "LOW",
    "SOURCE_UNAVAILABLE": "INFO",
    "SIMULATED_MISMATCH": "MEDIUM",
}


@dataclass(frozen=True)
class Compute:
    session: Session
    settings: Settings
    institution_id: UUID
    now: datetime
    academic_year: str | None = None
    programme_id: UUID | None = None


def signal(
    rule_id: str,
    family: Family,
    severity: Severity,
    key_parts: Iterable[object],
    title: str,
    calculation: str,
    action: str,
    *,
    evidence: EvidenceRefs | None = None,
    scope: SubmissionScope | None = None,
    programme_id: UUID | None = None,
) -> Signal:
    # Keys are filter-independent so a decision keeps matching across views.
    key = "|".join([rule_id, *(str(part) for part in key_parts)])
    return Signal(
        signal_key=key,
        rule_id=rule_id,
        family=family,
        severity=severity,
        title=title,
        calculation=calculation,
        evidence=evidence or EvidenceRefs(),
        programme_id=scope.programme_id if scope else programme_id,
        academic_year=scope.academic_year if scope else None,
        recommended_next_action=action,
    )


def capped_ids(ids: Iterable[object]) -> tuple[list[UUID], int]:
    unique = list(dict.fromkeys(UUID(str(item)) for item in ids))
    return unique[:RECORD_ID_CAP], len(unique)


def reference_batch(session: Session, scope: SubmissionScope) -> SubmissionBatch | None:
    """The current snapshot, else the latest processed batch in the scope."""
    if scope.current_batch_id is not None:
        return session.get(SubmissionBatch, scope.current_batch_id)
    return session.scalar(
        select(SubmissionBatch)
        .where(
            SubmissionBatch.scope_id == scope.id,
            SubmissionBatch.status == ProcessingStatus.COMPLETED,
        )
        .order_by(SubmissionBatch.completed_at.desc(), SubmissionBatch.id.desc())
        .limit(1)
    )


def finding_ids(rows: list[Any]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        if row.record_version_id is not None:
            ids.append(str(row.record_version_id))
        ids.extend(row.evidence_json_redacted.get("affected_record_ids", []))
    return ids


def data_quality_and_identity(
    ctx: Compute, scope: SubmissionScope, batch: SubmissionBatch
) -> list[Signal]:
    found: list[Signal] = []
    run = selected_run(ctx.session, batch.id)
    if run is not None:
        codes = {c for group in DQ_SOURCES.values() for c in group}
        rows = list(
            ctx.session.execute(
                select(
                    ValidationFinding.rule_code,
                    ValidationFinding.record_version_id,
                    ValidationFinding.evidence_json_redacted,
                ).where(
                    ValidationFinding.run_id == run.id,
                    ValidationFinding.rule_code.in_({*codes, CROSS_INSTITUTION_CODE}),
                )
            )
        )
        by_code: dict[str, list[Any]] = {}
        for row in rows:
            by_code.setdefault(row.rule_code, []).append(row)
        quality: dict[str, tuple[str, str, Severity]] = {
            "DQ_MISSING_FIELDS": (
                "Required fields are missing",
                "Ask the institution to complete the listed fields and resubmit.",
                "MEDIUM",
            ),
            "DQ_MALFORMED_APAAR": (
                "APAAR values fail the configured local format check",
                "Ask the institution to correct the values. The check is "
                "structural only and is not verification.",
                "LOW",
            ),
            "DQ_DUPLICATE_IDENTIFIERS": (
                "Repeated identifiers within the latest validated batch",
                "Review the linked records; repeats make counts ambiguous and "
                "nothing was merged or removed.",
                "MEDIUM",
            ),
        }
        for rule_id, (title, action, severity) in quality.items():
            matched = [r for code in DQ_SOURCES[rule_id] for r in by_code.get(code, [])]
            if not matched:
                continue
            ids, total = capped_ids(finding_ids(matched))
            counts = {c: len(by_code[c]) for c in DQ_SOURCES[rule_id] if c in by_code}
            found.append(
                signal(
                    rule_id,
                    "DATA_QUALITY",
                    severity,
                    [scope.id],
                    title,
                    f"{len(matched)} finding(s) touching {total} record(s) in the "
                    f"latest completed validation run of batch {batch.id}.",
                    action,
                    evidence=EvidenceRefs(
                        batch_ids=[batch.id],
                        validation_run_id=run.id,
                        finding_rule_counts=counts,
                        record_version_ids=ids,
                        record_version_total=total,
                    ),
                    scope=scope,
                )
            )
        cross = by_code.get(CROSS_INSTITUTION_CODE, [])
        if cross:
            current = sum(
                r.evidence_json_redacted.get("match_context") == "CURRENT_ACTIVE"
                for r in cross
            )
            ids, total = capped_ids(finding_ids(cross))
            found.append(
                signal(
                    "IDU_CROSS_INSTITUTION_DUPLICATE",
                    "IDENTITY_UNCERTAINTY",
                    "MEDIUM" if current else "INFO",
                    [scope.id],
                    "Potential duplicate with another institution",
                    f"{len(cross)} potential match finding(s) touching {total} "
                    f"record(s): {current} with potential current ACTIVE overlap, "
                    f"{len(cross) - current} informational. A transfer or "
                    "withdrawal may explain a match; this is not a duplicate "
                    "determination.",
                    "Review the linked records and any transfer or withdrawal "
                    "explanation before opening a case.",
                    evidence=EvidenceRefs(
                        batch_ids=[batch.id],
                        validation_run_id=run.id,
                        finding_rule_counts={CROSS_INSTITUTION_CODE: len(cross)},
                        record_version_ids=ids,
                        record_version_total=total,
                    ),
                    scope=scope,
                )
            )
    latest = ctx.session.execute(
        select(ApaarVerification.record_version_id, ApaarVerification.status)
        .where(ApaarVerification.batch_id == batch.id)
        .ext(distinct_on(ApaarVerification.record_version_id))
        .order_by(
            ApaarVerification.record_version_id,
            ApaarVerification.requested_at.desc(),
            ApaarVerification.id.desc(),
        )
    )
    grouped: dict[str, list[UUID]] = {}
    for record_id, status in latest:
        grouped.setdefault(status, []).append(record_id)
    for status, severity in VERIFICATION_SEVERITY.items():
        records = grouped.get(status, [])
        if not records:
            continue
        ids, total = capped_ids(records)
        label = "MISMATCH" if status == "SIMULATED_MISMATCH" else status
        found.append(
            signal(
                "IDU_VERIFICATION_UNRESOLVED",
                "IDENTITY_UNCERTAINTY",
                severity,
                [scope.id, status],
                f"SIMULATED / DEMO DATA: verification {label} for {total} record(s)",
                f"{total} record(s) whose latest SIMULATED verification is "
                f"{label}. Statuses are counted separately: SOURCE_UNAVAILABLE "
                "means no answer was available and is not a mismatch.",
                "Re-request the simulated check or review the records; this is "
                "not official APAAR verification.",
                evidence=EvidenceRefs(
                    batch_ids=[batch.id],
                    record_version_ids=ids,
                    record_version_total=total,
                ),
                scope=scope,
            )
        )
    return found


def latest_assessment(
    session: Session, scope: SubmissionScope
) -> IntakeAssessment | None:
    return session.scalar(
        select(IntakeAssessment)
        .where(
            IntakeAssessment.institution_id == scope.institution_id,
            IntakeAssessment.programme_id == scope.programme_id,
            IntakeAssessment.academic_year == scope.academic_year,
        )
        .order_by(IntakeAssessment.computed_at.desc(), IntakeAssessment.id.desc())
        .limit(1)
    )


def change_pair(
    session: Session, scope: SubmissionScope
) -> tuple[SubmissionBatch, SubmissionBatch] | None:
    """(newer, prior): pending candidate vs current, else latest activation vs prior."""
    if scope.current_batch_id is None:
        return None
    current = session.get(SubmissionBatch, scope.current_batch_id)
    assert current is not None
    candidate = session.scalar(
        select(SubmissionBatch)
        .where(
            SubmissionBatch.scope_id == scope.id,
            SubmissionBatch.status == ProcessingStatus.COMPLETED,
            SubmissionBatch.activated_at.is_(None),
            SubmissionBatch.completed_at > current.completed_at,
        )
        .order_by(SubmissionBatch.completed_at.desc(), SubmissionBatch.id.desc())
        .limit(1)
    )
    if candidate is not None:
        return candidate, current
    review = (
        session.get(SubmissionReview, current.activation_review_id)
        if current.activation_review_id
        else None
    )
    if review is None or review.expected_current_batch_id is None:
        return None
    prior = session.get(SubmissionBatch, review.expected_current_batch_id)
    return (current, prior) if prior is not None else None


def compliance_for_scope(
    ctx: Compute, scope: SubmissionScope, batch: SubmissionBatch | None
) -> list[Signal]:
    found: list[Signal] = []
    session = ctx.session
    assessment = latest_assessment(session, scope)
    if batch is not None:
        rules = configured_rules(
            session,
            scope.institution_id,
            scope.programme_id,
            scope.academic_year,
            ctx.settings.validation_intake_rule_version,
        )
        active = active_by_category(batch_rows(session, batch.id))
        for category in CATEGORIES:
            line = capacity_line(
                category, rules.get(category), active[category], "ACTIVE"
            )
            if line["exceeded"]:
                found.append(
                    signal(
                        "CMP_INTAKE_EXCEEDED",
                        "COMPLIANCE",
                        "HIGH",
                        [scope.id, category],
                        f"ACTIVE records exceed configured DEMO capacity ({category})",
                        f"{line['calculation']}. Capacity is per category and "
                        "DEMO-configured; not official policy.",
                        "Check the DEMO rule and the records' category and status "
                        "before any follow-up.",
                        evidence=EvidenceRefs(
                            batch_ids=[batch.id],
                            finding_rule_counts={"INTAKE_CATEGORY_EXCEEDED": 1},
                            assessment_id=assessment.id if assessment else None,
                        ),
                        scope=scope,
                    )
                )
    if scope.current_batch_id is not None and (
        latest_declaration(
            session, scope.institution_id, scope.programme_id, scope.academic_year
        )
        is None
    ):
        found.append(
            signal(
                "CMP_MISSING_DECLARATION",
                "COMPLIANCE",
                "LOW",
                [scope.id],
                "No declared admission total on file",
                "A current snapshot exists but no DEMO declaration does. This is "
                "not zero enrolment and no shortfall can be computed.",
                "Ask the institution to record a declared total.",
                evidence=EvidenceRefs(batch_ids=[scope.current_batch_id]),
                scope=scope,
            )
        )
    population = assessment.result.get("missing_population") if assessment else None
    if population and population.get("discrepancy"):
        found.append(
            signal(
                "CMP_MISSING_POPULATION",
                "COMPLIANCE",
                "MEDIUM",
                [scope.id],
                "Submitted records fall short of the declared total",
                f"{population['calculation']}. A shortfall is a comparison with a "
                "DEMO declaration, not proof that records are missing.",
                "Compare the declaration and the submission with the institution.",
                evidence=EvidenceRefs(
                    batch_ids=[assessment.batch_id] if assessment else [],
                    assessment_id=assessment.id if assessment else None,
                    finding_rule_counts={"MISSING_POPULATION_DISCREPANCY": 1},
                ),
                scope=scope,
            )
        )
    pair = change_pair(session, scope)
    if pair is not None:
        newer, prior = pair
        prior_rows = batch_rows(session, prior.id)
        diff = snapshot_diff(prior_rows, batch_rows(session, newer.id))
        if diff["status"] == "COMPARED" and prior_rows:
            removed, changed = diff["removed_count"], diff["changed_count"]
            ratio = (removed + changed) / len(prior_rows)
            threshold = ctx.settings.integrity_change_ratio_threshold
            if ratio >= threshold:
                found.append(
                    signal(
                        "CMP_UNUSUAL_SNAPSHOT_CHANGE",
                        "COMPLIANCE",
                        "MEDIUM",
                        [scope.id],
                        "Large share of prior snapshot removed or changed",
                        f"{removed} removed + {changed} changed of {len(prior_rows)} "
                        f"prior records = {ratio:.1%} >= threshold {threshold:.1%}. "
                        "Omission is not proof of withdrawal or transfer.",
                        "Ask the institution to explain the differences between "
                        "the two submissions.",
                        evidence=EvidenceRefs(batch_ids=[newer.id, prior.id]),
                        scope=scope,
                    )
                )
    return found


def case_signals(ctx: Compute) -> list[Signal]:
    statement = select(ReviewCase).where(
        ReviewCase.institution_id == ctx.institution_id
    )
    if ctx.academic_year or ctx.programme_id:
        linked = (
            select(CaseRecord.case_id)
            .join(SubmissionBatch, SubmissionBatch.id == CaseRecord.batch_id)
            .where(SubmissionBatch.institution_id == ctx.institution_id)
        )
        if ctx.academic_year:
            linked = linked.where(SubmissionBatch.academic_year == ctx.academic_year)
        if ctx.programme_id:
            linked = linked.where(SubmissionBatch.programme_id == ctx.programme_id)
        statement = statement.where(ReviewCase.id.in_(linked))
    cases = list(ctx.session.scalars(statement.order_by(ReviewCase.opened_at)))
    if not cases:
        return []
    found: list[Signal] = []
    threshold = ctx.settings.integrity_repeated_corrections_threshold
    corrections: Counter[UUID] = Counter(
        dict(
            ctx.session.execute(
                select(CaseEvent.case_id, func.count())
                .where(
                    CaseEvent.action == "REQUEST_CORRECTION",
                    CaseEvent.case_id.in_([c.id for c in cases]),
                )
                .group_by(CaseEvent.case_id)
            ).all()
        )
    )
    per_case = [case for case in cases if corrections[case.id] >= threshold]
    for case in per_case:
        found.append(
            signal(
                "CMP_REPEATED_CORRECTIONS",
                "COMPLIANCE",
                "LOW",
                ["case", case.id],
                "Repeated correction requests on one case",
                f"{corrections[case.id]} correction request(s) on this case "
                f">= threshold {threshold}.",
                "Review the case history and whether the requests were clear.",
                evidence=EvidenceRefs(
                    case_ids=[case.id],
                    finding_rule_counts={"REQUEST_CORRECTION": corrections[case.id]},
                ),
            )
        )
    total = sum(corrections.values())
    if not per_case and total >= threshold:
        with_requests = [c.id for c in cases if corrections[c.id]]
        found.append(
            signal(
                "CMP_REPEATED_CORRECTIONS",
                "COMPLIANCE",
                "LOW",
                ["institution"],
                "Repeated correction requests across cases",
                f"{total} correction request(s) over {len(with_requests)} case(s) "
                f">= threshold {threshold}; no single case reached it.",
                "Review whether recurring issues share a cause.",
                evidence=EvidenceRefs(
                    case_ids=with_requests[:CASE_ID_CAP],
                    finding_rule_counts={"REQUEST_CORRECTION": total},
                ),
            )
        )
    flags = [(case, case_flags(case, ctx.settings, ctx.now)) for case in cases]
    overdue = [(case, flag) for case, flag in flags if flag[0]]
    if overdue:
        escalated = sum(flag[1] for _, flag in overdue)
        found.append(
            signal(
                "CMP_OVERDUE_CASES",
                "COMPLIANCE",
                "HIGH" if escalated else "MEDIUM",
                ["institution"],
                "Review cases are past their due date",
                f"{len(overdue)} open case(s) past due, {escalated} of them past "
                "the escalation window.",
                "Follow up on overdue cases and reassign or extend as needed.",
                evidence=EvidenceRefs(
                    case_ids=[case.id for case, _ in overdue][:CASE_ID_CAP]
                ),
            )
        )
    return found


def stale_signals(ctx: Compute) -> list[Signal]:
    # Programme-level: the academic_year filter does not apply.
    programmes = select(Programme).where(
        Programme.institution_id == ctx.institution_id, Programme.active.is_(True)
    )
    if ctx.programme_id:
        programmes = programmes.where(Programme.id == ctx.programme_id)
    latest = {
        row.programme_id: row
        for row in ctx.session.execute(
            select(SubmissionBatch.programme_id, SubmissionBatch.id)
            .where(
                SubmissionBatch.institution_id == ctx.institution_id,
                SubmissionBatch.activated_at.is_not(None),
            )
            .ext(distinct_on(SubmissionBatch.programme_id))
            .order_by(
                SubmissionBatch.programme_id,
                SubmissionBatch.activated_at.desc(),
                SubmissionBatch.id.desc(),
            )
        )
    }
    activated_at = dict(
        ctx.session.execute(
            select(SubmissionBatch.id, SubmissionBatch.activated_at).where(
                SubmissionBatch.id.in_([r.id for r in latest.values()])
            )
        ).all()
    )
    days = ctx.settings.integrity_stale_days
    found: list[Signal] = []
    for programme in ctx.session.scalars(programmes.order_by(Programme.code)):
        row = latest.get(programme.id)
        stamp = activated_at.get(row.id) if row else None
        if stamp is not None and ctx.now - stamp <= timedelta(days=days):
            continue
        age = (
            f"last activated snapshot is {(ctx.now - stamp).days} day(s) old"
            if stamp is not None
            else "no activated snapshot is on record"
        )
        found.append(
            signal(
                "CMP_STALE_SUBMISSION",
                "COMPLIANCE",
                "LOW",
                [programme.id],
                "No recent activated snapshot for a programme",
                f"{age}; threshold is {days} day(s). Missing data is unknown, "
                "not zero enrolment.",
                "Ask the institution whether a submission is due.",
                evidence=EvidenceRefs(batch_ids=[row.id] if row else []),
                programme_id=programme.id,
            )
        )
    return found


def compute_signals(ctx: Compute) -> list[Signal]:
    statement = select(SubmissionScope).where(
        SubmissionScope.institution_id == ctx.institution_id
    )
    if ctx.academic_year:
        statement = statement.where(SubmissionScope.academic_year == ctx.academic_year)
    if ctx.programme_id:
        statement = statement.where(SubmissionScope.programme_id == ctx.programme_id)
    found: list[Signal] = []
    scopes = ctx.session.scalars(
        statement.order_by(SubmissionScope.academic_year, SubmissionScope.programme_id)
    )
    for scope in scopes:
        batch = reference_batch(ctx.session, scope)
        if batch is not None:
            found += data_quality_and_identity(ctx, scope, batch)
        found += compliance_for_scope(ctx, scope, batch)
    found += case_signals(ctx)
    found += stale_signals(ctx)
    decisions = latest_decisions(ctx.session, ctx.institution_id)
    for item in found:
        decision = decisions.get(item.signal_key)
        if decision is not None:
            item.decision = decision.decision  # type: ignore[assignment]
            item.decision_at = decision.created_at
            item.dismissed = decision.decision == "FALSE_POSITIVE"
    found.sort(
        key=lambda s: (
            -SEVERITY_RANK[s.severity],
            FAMILIES.index(s.family),
            s.rule_id,
            s.signal_key,
        )
    )
    return found


def latest_decisions(
    session: Session, institution_id: UUID
) -> dict[str, IntegrityDecision]:
    rows = session.scalars(
        select(IntegrityDecision)
        .where(IntegrityDecision.institution_id == institution_id)
        .ext(distinct_on(IntegrityDecision.signal_key))
        .order_by(
            IntegrityDecision.signal_key,
            IntegrityDecision.created_at.desc(),
            IntegrityDecision.id.desc(),
        )
    )
    return {row.signal_key: row for row in rows}


def build_score(signals: list[Signal], settings: Settings) -> ScoreSummary:
    weights = settings.integrity_severity_weights
    components: list[FamilyScore] = []
    for family in FAMILIES:
        members = [s for s in signals if s.family == family]
        active = [s for s in members if not s.dismissed]
        components.append(
            FamilyScore(
                family=family,
                signal_count=len(members),
                active_count=len(active),
                weighted_points=sum(weights[s.severity] for s in active),
                max_severity=max(
                    (s.severity for s in active),
                    key=SEVERITY_RANK.__getitem__,
                    default=None,
                ),
            )
        )
    total = sum(c.weighted_points for c in components)
    high, medium = (
        settings.integrity_band_high_points,
        settings.integrity_band_medium_points,
    )
    band: Band = "HIGH" if total >= high else "MEDIUM" if total >= medium else "LOW"
    return ScoreSummary(
        components=components,
        total_points=total,
        band=band,
        severity_weights=dict(weights),
        band_thresholds={"MEDIUM": medium, "HIGH": high},
    )


def parameters(settings: Settings) -> dict[str, float | int]:
    return {
        "change_ratio_threshold": settings.integrity_change_ratio_threshold,
        "repeated_corrections_threshold": (
            settings.integrity_repeated_corrections_threshold
        ),
        "stale_days": settings.integrity_stale_days,
    }


def institution_signals(
    session: Session,
    settings: Settings,
    user: User,
    institution_id: UUID,
    now: datetime,
    academic_year: str | None,
    programme_id: UUID | None,
) -> SignalsResponse:
    intake_actor(session, user, institution_id)
    if programme_id is not None:
        scoped_programme(session, institution_id, programme_id)
    signals = compute_signals(
        Compute(session, settings, institution_id, now, academic_year, programme_id)
    )
    return SignalsResponse(
        institution_id=institution_id,
        academic_year=academic_year,
        programme_id=programme_id,
        generated_at=now,
        parameters=parameters(settings),
        score=build_score(signals, settings),
        signals=signals,
    )


def overview(
    session: Session,
    settings: Settings,
    now: datetime,
    academic_year: str | None,
    band: Band | None,
    page: int,
    page_size: int,
) -> OverviewResponse:
    """Aggregates only. Computed per institution, which suits a small prototype."""
    items: list[OverviewItem] = []
    for institution in session.scalars(
        select(Institution).where(Institution.active.is_(True))
    ):
        signals = compute_signals(
            Compute(session, settings, institution.id, now, academic_year)
        )
        score = build_score(signals, settings)
        if band is not None and score.band != band:
            continue
        dismissed = sum(s.dismissed for s in signals)
        items.append(
            OverviewItem(
                institution_id=institution.id,
                institution_name=institution.name,
                signal_count=len(signals),
                active_count=len(signals) - dismissed,
                dismissed_count=dismissed,
                score=score,
            )
        )
    items.sort(
        key=lambda i: (-i.score.total_points, i.institution_name, str(i.institution_id))
    )
    window = paginate_list(items, page, page_size)
    return OverviewResponse(
        generated_at=now,
        academic_year=academic_year,
        band=band,
        data=window.data,
        pagination=window.pagination,
    )


def record_decision(
    session: Session,
    settings: Settings,
    user: User,
    institution_id: UUID,
    request: DecisionRequest,
    now: datetime,
) -> IntegrityDecision:
    try:
        intake_actor(session, user, institution_id, officer_only=True)
        current = {
            s.signal_key: s
            for s in compute_signals(Compute(session, settings, institution_id, now))
        }
        target = current.get(request.signal_key)
        if target is None:
            raise APIError(
                422,
                "UNKNOWN_SIGNAL",
                "signal_key is not a currently computed signal of this institution",
            )
        decision = IntegrityDecision(
            institution_id=institution_id,
            signal_key=request.signal_key,
            decision=request.decision,
            reason=request.reason,
            decided_by=user.id,
        )
        session.add(decision)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=institution_id,
            action="INTEGRITY_DECISION_RECORDED",
            entity_type="integrity_decisions",
            entity_id=decision.id,
            details={"decision": request.decision, "rule_id": target.rule_id},
        )
        session.commit()
        return decision
    except Exception:
        session.rollback()
        raise
