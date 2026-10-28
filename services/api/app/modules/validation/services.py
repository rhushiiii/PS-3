import csv
import io
from collections import Counter
from datetime import UTC, datetime
from time import monotonic
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_snapshot_session
from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.institutions.models import IntakeRule, Programme
from app.modules.institutions.services import scoped_institution
from app.modules.submissions.models import (
    ProcessingStatus,
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.services import row_response, scoped_batch
from app.modules.validation.models import ValidationFinding, ValidationRun
from app.modules.validation.rules import (
    CATEGORIES,
    RULESET_VERSION,
    STATUSES,
    STRUCTURAL_RULESET_VERSION,
    evaluate,
    valid_token,
)
from app.modules.validation.schemas import FindingResponse, RecordStatus, RunResponse

get_validation_session = get_snapshot_session


def scope_map(session: Session, year: str) -> dict[str, Any]:
    return {
        str(scope.id): {
            "revision": scope.revision,
            "current_batch_id": str(scope.current_batch_id)
            if scope.current_batch_id
            else None,
        }
        for scope in session.scalars(
            select(SubmissionScope).where(SubmissionScope.academic_year == year)
        )
    }


def selected_run(
    session: Session, batch_id: UUID, run_id: UUID | None = None
) -> ValidationRun | None:
    query = select(ValidationRun).where(ValidationRun.batch_id == batch_id)
    if run_id is not None:
        query = query.where(ValidationRun.id == run_id)
    run = session.scalar(
        query.order_by(
            ValidationRun.completed_at.desc(), ValidationRun.id.desc()
        ).limit(1)
    )
    if run is None and run_id is not None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return run


def require_run(
    session: Session, batch_id: UUID, run_id: UUID | None = None
) -> ValidationRun:
    run = selected_run(session, batch_id, run_id)
    if run is None:
        raise APIError(409, "VALIDATION_NOT_RUN", "No completed validation run exists")
    return run


def run_response(session: Session, run: ValidationRun) -> RunResponse:
    batch = session.get(SubmissionBatch, run.batch_id)
    assert batch is not None
    fresh = scope_map(session, batch.academic_year) == run.compared_scope_revisions_json
    complete = run.summary_json["matching_assessment"] == "COMPLETE"
    return RunResponse(
        id=run.id,
        batch_id=run.batch_id,
        kind=cast(Any, run.kind),
        requested_by=run.requested_by,
        evaluated_at=run.evaluated_at,
        completed_at=run.completed_at,
        ruleset_version=run.ruleset_version,
        ruleset_snapshot=run.ruleset_snapshot_json,
        summary=run.summary_json,
        cross_current_freshness="FRESH" if fresh else "STALE",
        current_overlap_records=run.summary_json[
            "current_overlap_records_at_evaluation"
        ]
        if fresh and complete
        else None,
    )


def findings_for(session: Session, run: ValidationRun) -> list[ValidationFinding]:
    return list(
        session.scalars(
            select(ValidationFinding)
            .where(ValidationFinding.run_id == run.id)
            .order_by(ValidationFinding.ordinal)
        )
    )


def record_statuses(findings: list[ValidationFinding]) -> dict[UUID, RecordStatus]:
    result: dict[UUID, RecordStatus] = {}
    for finding in findings:
        affected = (
            [finding.record_version_id]
            if finding.record_version_id
            else [
                UUID(value)
                for value in finding.evidence_json_redacted.get(
                    "affected_record_ids", []
                )
            ]
        )
        for record_id in affected:
            if finding.rule_code == "REQUIRED_FIELD_MISSING":
                result[record_id] = "INCOMPLETE"
            elif result.get(record_id) != "INCOMPLETE":
                result[record_id] = "FLAGGED"
    return result


def finding_response(
    finding: ValidationFinding, run: RunResponse, user: User
) -> FindingResponse:
    evidence = dict(finding.evidence_json_redacted)
    if user.role != Role.AICTE_OFFICER:
        evidence.pop("peer_references", None)
    return FindingResponse(
        id=finding.id,
        run_id=finding.run_id,
        batch_id=finding.batch_id,
        record_version_id=finding.record_version_id,
        ordinal=finding.ordinal,
        rule_code=finding.rule_code,
        severity=cast(Any, finding.severity),
        classification=cast(Any, finding.classification),
        field_name=finding.field_name,
        explanation=finding.explanation,
        evidence=evidence,
        evaluated_at=run.evaluated_at,
        cross_current_freshness=run.cross_current_freshness,
    )


def validate_candidate(
    session: Session,
    actor_id: UUID,
    batch_id: UUID,
    settings: Settings,
    *,
    revalidate: bool = False,
) -> RunResponse:
    deadline = monotonic() + settings.validation_processing_timeout_seconds

    def check_budget() -> None:
        if monotonic() >= deadline:
            raise APIError(
                422, "VALIDATION_LIMIT_EXCEEDED", "Validation processing budget expired"
            )

    try:
        user = session.get(User, actor_id)
        if user is None or not user.active:
            raise APIError(401, "UNAUTHENTICATED", "Authentication required")
        batch = scoped_batch(session, user, batch_id)
        scoped_institution(session, user, batch.institution_id)
        if revalidate and user.role != Role.AICTE_OFFICER:
            raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")
        if batch.status != ProcessingStatus.COMPLETED:
            raise APIError(
                409, "SUBMISSION_NOT_PROCESSED", "Candidate processing must be complete"
            )
        existing = selected_run(session, batch.id)
        if revalidate and existing is None:
            raise APIError(409, "VALIDATION_NOT_RUN", "Initial validation is required")
        if not revalidate and existing is not None:
            raise APIError(
                409, "VALIDATION_ALREADY_PERFORMED", "Initial validation already exists"
            )
        secret = settings.apaar_matching_key
        if secret is None or len(secret.get_secret_value().encode()) < 32:
            raise APIError(
                422,
                "MATCHING_CONFIGURATION_UNAVAILABLE",
                "APAAR matching requires an environment key of at least 32 bytes",
            )
        programme = session.get(Programme, batch.programme_id)
        assert programme is not None
        rows = list(
            session.scalars(
                select(StudentRecordVersion)
                .where(StudentRecordVersion.batch_id == batch.id)
                .order_by(StudentRecordVersion.source_row_number)
            )
        )
        if len(rows) != batch.row_count:
            raise APIError(
                409,
                "SUBMISSION_NOT_PROCESSED",
                "Candidate record count is inconsistent",
            )
        intake = list(
            session.scalars(
                select(IntakeRule)
                .where(
                    IntakeRule.institution_id == batch.institution_id,
                    IntakeRule.programme_id == batch.programme_id,
                    IntakeRule.academic_year == batch.academic_year,
                    IntakeRule.rule_version == settings.validation_intake_rule_version,
                    IntakeRule.source_label == "DEMO",
                )
                .order_by(IntakeRule.category)
            )
        )
        compared = scope_map(session, batch.academic_year)
        current = {
            value["current_batch_id"]
            for value in compared.values()
            if value["current_batch_id"]
        }
        peer_query = (
            select(StudentRecordVersion, SubmissionBatch)
            .join(SubmissionBatch, StudentRecordVersion.batch_id == SubmissionBatch.id)
            .where(
                StudentRecordVersion.institution_id != batch.institution_id,
                SubmissionBatch.status == ProcessingStatus.COMPLETED,
            )
            .order_by(
                StudentRecordVersion.batch_id, StudentRecordVersion.source_row_number
            )
        )
        # Count first; never silently truncate a comparison or report false zeroes.
        peer_count = (
            session.scalar(
                select(func.count()).select_from(peer_query.order_by(None).subquery())
            )
            or 0
        )
        if peer_count > settings.validation_max_comparison_records:
            raise APIError(
                422, "VALIDATION_LIMIT_EXCEEDED", "Comparison record limit exceeded"
            )
        evaluated_at = datetime.now(UTC)
        findings, summary = evaluate(
            rows,
            batch,
            programme.code,
            intake,
            (
                (peer, peer_batch)
                for peer, peer_batch in session.execute(
                    peer_query.execution_options(yield_per=500)
                )
            ),
            current,
            key=secret.get_secret_value().encode(),
            format_length=settings.apaar_format_length,
            check_budget=check_budget,
        )
        excluded = sum(
            not valid_token(
                row.apaar_identifier_encrypted_or_demo_token,
                settings.apaar_format_length,
            )
            for row in rows
        )
        summary.update(
            {
                "matching_excluded_candidate_records": excluded,
                "matching_assessment": "INCOMPLETE"
                if (
                    excluded
                    or summary["matching_excluded_current_peer_records"]
                    or summary["unclassifiable_records"]
                )
                else "COMPLETE",
                "current_overlap_count_basis": "FORMAT_VALID_MATCHES_AT_EVALUATION",
                "compared_record_versions": peer_count,
            }
        )
        run = ValidationRun(
            id=uuid4(),
            batch_id=batch.id,
            requested_by=user.id,
            kind="REVALIDATION" if revalidate else "INITIAL",
            evaluated_at=evaluated_at,
            completed_at=datetime.now(UTC),
            ruleset_version=RULESET_VERSION,
            ruleset_snapshot_json={
                "ruleset_version": RULESET_VERSION,
                "structural_ruleset_version": STRUCTURAL_RULESET_VERSION,
                "source_label": "DEMO",
                "apaar_ascii_digit_length": settings.apaar_format_length,
                "matching_algorithm": "HMAC-SHA256",
                "categories": list(CATEGORIES),
                "enrollment_statuses": list(STATUSES),
                "intake_rule_version": settings.validation_intake_rule_version,
                "programme_code": programme.code,
                "academic_year": batch.academic_year,
                "intake_rules": [
                    {
                        "id": str(rule.id),
                        "category": rule.category.value,
                        "approved_seats": rule.approved_seats,
                        "rule_version": rule.rule_version,
                        "source_label": rule.source_label,
                    }
                    for rule in intake
                ],
            },
            compared_scope_revisions_json=compared,
            summary_json=summary,
        )
        saved: list[ValidationFinding] = []
        for ordinal, finding in enumerate(findings, 1):
            check_budget()
            saved.append(
                ValidationFinding(
                    run_id=run.id,
                    batch_id=batch.id,
                    record_version_id=finding.record_id,
                    ordinal=ordinal,
                    rule_code=finding.code,
                    severity=finding.severity,
                    classification=finding.classification,
                    field_name=finding.field_name,
                    explanation=finding.explanation,
                    evidence_json_redacted=finding.evidence,
                )
            )
        status_counts = Counter(record_statuses(saved).values())
        # Set once, before persistence; never update completed run evidence.
        run.summary_json = {
            **summary,
            "record_status_counts": {
                "INCOMPLETE": status_counts["INCOMPLETE"],
                "FLAGGED": status_counts["FLAGGED"],
                "VALID": len(rows) - sum(status_counts.values()),
            },
            "finding_count": len(saved),
            "activation_blocking_finding_count": sum(
                f.classification == "ACTIVATION_BLOCKING" for f in saved
            ),
        }
        session.add(run)
        session.flush()
        session.add_all(saved)
        record_action(
            session,
            actor_id=user.id,
            institution_id=batch.institution_id,
            action="SUBMISSION_REVALIDATED" if revalidate else "SUBMISSION_VALIDATED",
            entity_type="validation_runs",
            entity_id=run.id,
        )
        session.flush()
        result = run_response(session, run)
        check_budget()
        session.commit()
        return result
    except IntegrityError as error:
        session.rollback()
        if (
            getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            == "uq_validation_initial"
        ):
            raise APIError(
                409, "VALIDATION_ALREADY_PERFORMED", "Initial validation already exists"
            ) from None
        raise
    except Exception:
        session.rollback()
        raise


def structurally_compatible(
    run: ValidationRun, batch: SubmissionBatch, programme: Programme
) -> bool:
    """Explicit legacy mapping; absence never means 'use today's rules'."""
    snapshot = run.ruleset_snapshot_json
    legacy = {"LOCAL-DEMO-v1": "LOCAL-STRUCTURE-DEMO-v1"}
    version = snapshot.get(
        "structural_ruleset_version", legacy.get(run.ruleset_version)
    )
    return bool(
        version == STRUCTURAL_RULESET_VERSION
        and snapshot.get("categories") == list(CATEGORIES)
        and snapshot.get("enrollment_statuses") == list(STATUSES)
        and snapshot.get("programme_code") == programme.code
        and snapshot.get("academic_year") == batch.academic_year
        and run.completed_at is not None
    )


def safe_csv_cell(value: object) -> str:
    text = str(value) if value is not None else ""
    # Prefix risky content, including formulas hidden behind whitespace/control chars.
    start = 0
    while start < len(text) and (
        text[start].isspace() or ord(text[start]) <= 32 or text[start] == "\ufeff"
    ):
        start += 1
    stripped = text[start:]
    return (
        "'" + text
        if (
            stripped.startswith(("=", "+", "-", "@"))
            or text.startswith(("\t", "\r", "\n"))
        )
        else text
    )


def feedback_csv(
    session: Session, batch: SubmissionBatch, run: ValidationRun, user: User
) -> str:
    description = run_response(session, run)
    findings = findings_for(session, run)
    statuses = record_statuses(findings)
    by_record: dict[UUID, list[ValidationFinding]] = {}
    batch_findings = []
    for finding in findings:
        affected = (
            [finding.record_version_id]
            if finding.record_version_id
            else [
                UUID(value)
                for value in finding.evidence_json_redacted.get(
                    "affected_record_ids", []
                )
            ]
        )
        if not affected:
            batch_findings.append(finding)
        for record_id in affected:
            by_record.setdefault(record_id, []).append(finding)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "run_id",
            "evaluated_at",
            "ruleset_version",
            "cross_current_freshness",
            "record_version_id",
            "source_row_number",
            "college_student_id",
            "apaar_id_masked",
            "validation_status",
            "rule_code",
            "severity",
            "classification",
            "field_name",
            "explanation",
        ]
    )

    def write(
        record: StudentRecordVersion | None, finding: ValidationFinding | None
    ) -> None:
        preview = row_response(record) if record else None
        writer.writerow(
            [
                safe_csv_cell(value)
                for value in [
                    run.id,
                    run.evaluated_at.isoformat(),
                    run.ruleset_version,
                    description.cross_current_freshness,
                    record.id if record else None,
                    record.source_row_number if record else None,
                    preview.college_student_id if preview else None,
                    preview.apaar_id_masked if preview else None,
                    statuses.get(record.id, "VALID") if record else None,
                    finding.rule_code if finding else None,
                    finding.severity if finding else None,
                    finding.classification if finding else None,
                    finding.field_name if finding else None,
                    finding.explanation
                    if finding
                    else "Passed local validation; not official APAAR verification",
                ]
            ]
        )

    for record in session.scalars(
        select(StudentRecordVersion)
        .where(StudentRecordVersion.batch_id == batch.id)
        .order_by(StudentRecordVersion.source_row_number)
    ):
        record_findings = by_record.get(record.id)
        if record_findings:
            for record_finding in record_findings:
                write(record, record_finding)
        else:
            write(record, None)
    for finding in batch_findings:
        write(None, finding)
    return output.getvalue()
