"""Intake governance: DEMO rule changes, declared totals, assessments, simulation.

Category semantics mirror validation: capacity is per academic year, programme and
seat category, and categories are never pooled into one cap.
"""

from collections import Counter
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.core.http import APIError, not_found
from app.modules.audit.services import record_action
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import Role, User
from app.modules.institutions.models import Institution, IntakeRule
from app.modules.institutions.services import scoped_institution, scoped_programme
from app.modules.intake.models import (
    IntakeAssessment,
    IntakeDeclaration,
    IntakeRuleChange,
)
from app.modules.intake.schemas import (
    DEMO_NOTICE,
    AssessmentResponse,
    DeclarationRequest,
    RuleChangeRequest,
    SimulationRequest,
    SimulationResponse,
)
from app.modules.submissions.models import (
    ProcessingStatus,
    StudentRecordVersion,
    SubmissionScope,
)
from app.modules.submissions.parsing import HEADERS
from app.modules.submissions.services import batch_rows, scoped_batch, snapshot_counts
from app.modules.validation.rules import CATEGORIES

CHANGE_LIST_CAP = 200
POOLING_NOTE = (
    "Informational only: categories are not pooled and totals are never compared "
    "against a single cap."
)


def intake_actor(
    session: Session, user: User, institution_id: UUID, *, officer_only: bool = False
) -> Institution:
    """Officers: any institution. Admins: own institution only (else 404)."""
    allowed = {Role.AICTE_OFFICER} | (
        set() if officer_only else {Role.INSTITUTION_ADMIN}
    )
    require_roles(user, allowed)
    return scoped_institution(session, user, institution_id)


def configured_rules(
    session: Session,
    institution_id: UUID,
    programme_id: UUID,
    academic_year: str,
    rule_version: str,
) -> dict[str, IntakeRule]:
    # Same selection as validation: the configured version, DEMO rules only.
    return {
        rule.category.value: rule
        for rule in session.scalars(
            select(IntakeRule).where(
                IntakeRule.institution_id == institution_id,
                IntakeRule.programme_id == programme_id,
                IntakeRule.academic_year == academic_year,
                IntakeRule.rule_version == rule_version,
                IntakeRule.source_label == "DEMO",
            )
        )
    }


def active_by_category(rows: list[StudentRecordVersion]) -> dict[str, int]:
    categories = snapshot_counts(rows)["categories"]
    return {c: int(categories[c]["demo_active_records"]) for c in CATEGORIES}


def capacity_line(
    category: str, rule: IntakeRule | None, active: int, label: str
) -> dict[str, Any]:
    if rule is None:
        return {
            "category": category,
            "approved_seats": None,
            "rule_version": None,
            "remaining_capacity": None,
            "exceeded": False,
            "excess": 0,
            "calculation": (
                f"no DEMO rule configured for {category}; "
                "no capacity comparison or exceedance claim made"
            ),
        }
    approved = rule.approved_seats
    exceeded = active > approved
    excess = max(0, active - approved)
    return {
        "category": category,
        "approved_seats": approved,
        "rule_version": rule.rule_version,
        "remaining_capacity": approved - active,
        "exceeded": exceeded,
        "excess": excess,
        "calculation": (
            f"{label} {active} {'>' if exceeded else '<='} approved {approved} "
            f"(rule {rule.rule_version}, {category}) = excess {excess}"
        ),
    }


def latest_declaration(
    session: Session, institution_id: UUID, programme_id: UUID, academic_year: str
) -> IntakeDeclaration | None:
    return session.scalar(
        select(IntakeDeclaration)
        .where(
            IntakeDeclaration.institution_id == institution_id,
            IntakeDeclaration.programme_id == programme_id,
            IntakeDeclaration.academic_year == academic_year,
        )
        .order_by(IntakeDeclaration.created_at.desc(), IntakeDeclaration.id.desc())
        .limit(1)
    )


def latest_declarations_bulk(
    session: Session, programme_ids: list[UUID]
) -> dict[tuple[UUID, str], int]:
    # Same "latest wins" ordering as `latest_declaration`, in bulk.
    rows = session.execute(
        select(
            IntakeDeclaration.programme_id,
            IntakeDeclaration.academic_year,
            IntakeDeclaration.declared_total,
        )
        .where(IntakeDeclaration.programme_id.in_(programme_ids))
        .order_by(
            IntakeDeclaration.programme_id,
            IntakeDeclaration.academic_year,
            IntakeDeclaration.created_at.desc(),
            IntakeDeclaration.id.desc(),
        )
        .ext(
            distinct_on(IntakeDeclaration.programme_id, IntakeDeclaration.academic_year)
        )
    )
    return {(pid, year): total for pid, year, total in rows}


def change_rule(
    session: Session,
    user: User,
    institution_id: UUID,
    rule_id: UUID,
    request: RuleChangeRequest,
) -> IntakeRuleChange:
    """Update in place (keeps the validation-selected rule_version) and log it."""
    try:
        intake_actor(session, user, institution_id, officer_only=True)
        rule = session.scalar(
            select(IntakeRule)
            .where(
                IntakeRule.id == rule_id, IntakeRule.institution_id == institution_id
            )
            .with_for_update()
        )
        if rule is None:
            raise not_found()
        if rule.approved_seats == request.approved_seats:
            raise APIError(422, "NO_CHANGE", "Approved seats already have this value")
        change = IntakeRuleChange(
            intake_rule_id=rule.id,
            changed_by=user.id,
            old_approved_seats=rule.approved_seats,
            new_approved_seats=request.approved_seats,
            old_rule_version=rule.rule_version,
            new_rule_version=rule.rule_version,
            reason=request.reason,
        )
        rule.approved_seats = request.approved_seats
        session.add(change)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=institution_id,
            action="INTAKE_RULE_CHANGED",
            entity_type="intake_rule_changes",
            entity_id=change.id,
            details={
                "intake_rule_id": str(rule.id),
                "old_approved_seats": str(change.old_approved_seats),
                "new_approved_seats": str(change.new_approved_seats),
                "rule_version": rule.rule_version,
            },
        )
        session.commit()
        return change
    except Exception:
        session.rollback()
        raise


def declare(
    session: Session, user: User, institution_id: UUID, request: DeclarationRequest
) -> IntakeDeclaration:
    try:
        intake_actor(session, user, institution_id)
        scoped_programme(session, institution_id, request.programme_id)
        declaration = IntakeDeclaration(
            institution_id=institution_id,
            programme_id=request.programme_id,
            academic_year=request.academic_year,
            declared_total=request.declared_total,
            source_label="DEMO",
            basis=request.basis,
            declared_by=user.id,
        )
        session.add(declaration)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=institution_id,
            action="INTAKE_DECLARATION_CREATED",
            entity_type="intake_declarations",
            entity_id=declaration.id,
            details={
                "programme_id": str(request.programme_id),
                "academic_year": request.academic_year,
                "declared_total": str(request.declared_total),
            },
        )
        session.commit()
        return declaration
    except Exception:
        session.rollback()
        raise


def snapshot_diff(
    current: list[StudentRecordVersion] | None, candidate: list[StudentRecordVersion]
) -> dict[str, Any]:
    """Exact trimmed college_student_id comparison; never merges on APAAR."""
    if current is None:
        return {"status": "NO_CURRENT_SNAPSHOT"}
    before = {row.college_student_id: row for row in current}
    after = {row.college_student_id: row for row in candidate}
    if (
        len(before) != len(current)
        or len(after) != len(candidate)
        or "" in before
        or "" in after
    ):
        return {"status": "UNAVAILABLE_AMBIGUOUS_IDENTIFIERS"}
    fields = [name for name in HEADERS if name != "college_student_id"]
    changes: list[dict[str, Any]] = []
    removed_active = 0
    counts: Counter[str] = Counter()
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        changed: list[str]
        if old is None:
            kind, changed = "ADDED", []
        elif new is None:
            kind, changed = "REMOVED", []
            removed_active += old.enrollment_status == "ACTIVE"
        else:
            changed = [
                name
                for name in fields
                if old.normalized_json.get(name) != new.normalized_json.get(name)
            ]
            if not changed:
                counts["RETAINED"] += 1
                continue
            kind = "CHANGED"
        counts[kind] += 1
        # Field names only: no APAAR, names or other values leave the diff.
        changes.append(
            {"college_student_id": key, "change_type": kind, "changed_fields": changed}
        )
    return {
        "status": "COMPARED",
        "added_count": counts["ADDED"],
        "removed_count": counts["REMOVED"],
        "changed_count": counts["CHANGED"],
        "retained_unchanged_count": counts["RETAINED"],
        "removed_active_count": removed_active,
        "changes_total": len(changes),
        "changes_truncated": len(changes) > CHANGE_LIST_CAP,
        "changes": changes[:CHANGE_LIST_CAP],
        "omission_meaning": (
            "Absent from candidate; not inferred withdrawal or transfer"
        ),
    }


def create_assessment(
    session: Session, user: User, batch_id: UUID, rule_version: str
) -> AssessmentResponse:
    try:
        batch = scoped_batch(session, user, batch_id)
        if batch.status != ProcessingStatus.COMPLETED:
            raise APIError(409, "SUBMISSION_NOT_PROCESSED", "Batch is not processed")
        rows = batch_rows(session, batch.id)
        if len(rows) != batch.row_count:
            raise APIError(409, "SUBMISSION_NOT_PROCESSED", "Record count inconsistent")
        scope = session.get(SubmissionScope, batch.scope_id, populate_existing=True)
        assert scope is not None
        current = (
            batch_rows(session, scope.current_batch_id)
            if scope.current_batch_id
            else None
        )
        rules = configured_rules(
            session,
            batch.institution_id,
            batch.programme_id,
            batch.academic_year,
            rule_version,
        )
        candidate_active = active_by_category(rows)
        current_active = active_by_category(current) if current is not None else None
        categories: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []
        for category in CATEGORIES:
            line = capacity_line(
                category,
                rules.get(category),
                candidate_active[category],
                "candidate ACTIVE",
            )
            line["current_active_count"] = (
                current_active[category] if current_active is not None else None
            )
            line["candidate_active_count"] = candidate_active[category]
            categories.append(line)
            if line["exceeded"]:
                findings.append(
                    {
                        "rule_id": "INTAKE_CATEGORY_EXCEEDED",
                        "severity": "WARNING",
                        "category": category,
                        "calculation": line["calculation"],
                        "rule_version": line["rule_version"],
                    }
                )
        diff = snapshot_diff(current, rows)
        declaration = latest_declaration(
            session, batch.institution_id, batch.programme_id, batch.academic_year
        )
        candidate_count = len(rows)
        population: dict[str, Any]
        shortfall = 0
        if declaration is None:
            population = {"status": "NO_REFERENCE"}
        else:
            declared = declaration.declared_total
            shortfall = max(0, declared - candidate_count)
            calculation = (
                f"candidate records {candidate_count} "
                f"{'<' if shortfall else '>='} declared {declared} "
                f"(DEMO declaration) = shortfall {shortfall}"
            )
            population = {
                "status": "COMPARED",
                "declaration_id": str(declaration.id),
                "declared_total": declared,
                "candidate_record_count": candidate_count,
                "shortfall": shortfall,
                "discrepancy": shortfall > 0,
                "calculation": calculation,
            }
            if shortfall:
                findings.append(
                    {
                        "rule_id": "MISSING_POPULATION_DISCREPANCY",
                        "severity": "WARNING",
                        "calculation": calculation,
                        "rule_version": rule_version,
                    }
                )
        diff["removed_conclusion"] = "NOT_ASSESSED"
        if diff["status"] == "COMPARED":
            removed_active = diff["removed_active_count"]
            if declaration is None:
                diff["removed_conclusion"] = "NO_REFERENCE"
            elif removed_active and shortfall:
                diff["removed_conclusion"] = "REMOVED_RECORDS_UNEXPLAINED"
                findings.append(
                    {
                        "rule_id": "REMOVED_RECORDS_UNEXPLAINED",
                        "severity": "WARNING",
                        "calculation": (
                            f"{removed_active} previously ACTIVE record(s) omitted; "
                            f"candidate records {candidate_count} < declared "
                            f"{declaration.declared_total} = shortfall {shortfall}"
                        ),
                        "removed_active_count": removed_active,
                        "removed_count": diff["removed_count"],
                        "rule_version": rule_version,
                    }
                )
            else:
                diff["removed_conclusion"] = "NO_CONCLUSION"
        result: dict[str, Any] = {
            "source_label": "DEMO",
            "notice": DEMO_NOTICE,
            "rule_version": rule_version,
            "is_current_snapshot": scope.current_batch_id == batch.id,
            "categories": categories,
            "totals": {
                "candidate_record_count": candidate_count,
                "candidate_active_count": sum(candidate_active.values()),
                "current_active_count": sum(current_active.values())
                if current_active is not None
                else None,
                "approved_seats_configured_sum": sum(
                    r.approved_seats for r in rules.values()
                ),
                "note": POOLING_NOTE,
            },
            "snapshot_diff": diff,
            "missing_population": population,
            "findings": findings,
        }
        assessment = IntakeAssessment(
            batch_id=batch.id,
            institution_id=batch.institution_id,
            programme_id=batch.programme_id,
            academic_year=batch.academic_year,
            scope_revision=scope.revision,
            current_batch_id=scope.current_batch_id,
            computed_by=user.id,
            rule_version=rule_version,
            result=result,
        )
        session.add(assessment)
        session.flush()
        record_action(
            session,
            actor_id=user.id,
            institution_id=batch.institution_id,
            action="INTAKE_ASSESSMENT_CREATED",
            entity_type="intake_assessments",
            entity_id=assessment.id,
            details={"batch_id": str(batch.id), "finding_count": str(len(findings))},
        )
        response = AssessmentResponse.model_validate(assessment)
        session.commit()
        return response
    except Exception:
        session.rollback()
        raise


def scoped_assessment(
    session: Session, user: User, batch_id: UUID, assessment_id: UUID
) -> IntakeAssessment:
    scoped_batch(session, user, batch_id)
    assessment = session.scalar(
        select(IntakeAssessment).where(
            IntakeAssessment.id == assessment_id, IntakeAssessment.batch_id == batch_id
        )
    )
    if assessment is None:
        raise not_found()
    return assessment


def simulate(
    session: Session,
    user: User,
    institution_id: UUID,
    request: SimulationRequest,
    rule_version: str,
) -> SimulationResponse:
    """Read-only against domain tables; only an audit event is written."""
    try:
        intake_actor(session, user, institution_id)
        scoped_programme(session, institution_id, request.programme_id)
        scope = session.scalar(
            select(SubmissionScope).where(
                SubmissionScope.institution_id == institution_id,
                SubmissionScope.programme_id == request.programme_id,
                SubmissionScope.academic_year == request.academic_year,
            )
        )
        current_id = scope.current_batch_id if scope else None
        before = (
            active_by_category(batch_rows(session, current_id))
            if current_id
            else dict.fromkeys(CATEGORIES, 0)
        )
        added: Counter[str] = Counter()
        for addition in request.additions:
            added[addition.category.value] += addition.count
        rules = configured_rules(
            session,
            institution_id,
            request.programme_id,
            request.academic_year,
            rule_version,
        )
        categories = []
        for category in CATEGORIES:
            after = before[category] + added[category]
            line = capacity_line(category, rules.get(category), after, "after ACTIVE")
            exceeded = line.pop("exceeded")
            categories.append(
                {
                    **line,
                    "before_active_count": before[category],
                    "added_count": added[category],
                    "after_active_count": after,
                    "would_exceed": exceeded,
                }
            )
        record_action(
            session,
            actor_id=user.id,
            institution_id=institution_id,
            action="INTAKE_SIMULATED",
            entity_type="institutions",
            entity_id=institution_id,
            details={
                "programme_id": str(request.programme_id),
                "academic_year": request.academic_year,
            },
        )
        session.commit()
        return SimulationResponse(
            institution_id=institution_id,
            programme_id=request.programme_id,
            academic_year=request.academic_year,
            has_current_snapshot=current_id is not None,
            current_batch_id=current_id,
            rule_version=rule_version,
            categories=categories,
        )
    except Exception:
        session.rollback()
        raise
