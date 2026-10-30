from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.institutions.models import Programme
from app.modules.institutions.services import scoped_institution, scoped_programme
from app.modules.submissions.models import (
    ProcessingStatus,
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.parsing import ParsedRow, check_budget
from app.modules.submissions.schemas import (
    BatchResponse,
    RowResponse,
    UploadContext,
    UploadResponse,
)
from app.modules.validation.rules import CATEGORIES, STATUSES


def snapshot_counts(rows: list[StudentRecordVersion]) -> dict[str, Any]:
    """Declared rows, not deduplicated people or official accounting policy."""
    categories = {
        category: {"declared_records": 0, "demo_active_records": 0}
        for category in CATEGORIES
    }
    statuses: Counter[str] = Counter()
    unclassified = 0
    for row in rows:
        status = (
            row.enrollment_status
            if row.enrollment_status in STATUSES
            else "UNSUPPORTED"
        )
        statuses[status] += 1
        if row.admission_category in categories:
            categories[row.admission_category]["declared_records"] += 1
            categories[row.admission_category]["demo_active_records"] += (
                row.enrollment_status == "ACTIVE"
            )
        else:
            unclassified += 1
    return {
        "declared_records": len(rows),
        "demo_active_records": statuses["ACTIVE"],
        "categories": categories,
        "statuses": {status: statuses[status] for status in (*STATUSES, "UNSUPPORTED")},
        "unclassified_category_records": unclassified,
    }


def batch_rows(session: Session, batch_id: UUID) -> list[StudentRecordVersion]:
    return list(
        session.scalars(
            select(StudentRecordVersion)
            .where(StudentRecordVersion.batch_id == batch_id)
            .order_by(StudentRecordVersion.source_row_number)
        )
    )


def require_submission_role(user: User, *, uploading: bool = False) -> None:
    allowed = (
        {Role.INSTITUTION_ADMIN}
        if uploading
        else {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER}
    )
    if user.role not in allowed:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")


def upload_scope(session: Session, user: User, context: UploadContext) -> None:
    require_submission_role(user, uploading=True)
    institution = scoped_institution(session, user, context.institution_id)
    scoped_programme(session, context.institution_id, context.programme_id)
    programme = session.get(Programme, context.programme_id)
    if not institution.active or programme is None or not programme.active:
        raise APIError(422, "INVALID_REQUEST", "Upload scope is inactive")


def upload_fingerprint(data: bytes, context: UploadContext) -> str:
    """Binds an idempotency key to the exact file and scope it first carried."""
    parts = (
        sha256(data).hexdigest(),
        str(context.institution_id),
        str(context.programme_id),
        context.academic_year,
        context.schema_version,
    )
    return sha256("|".join(parts).encode()).hexdigest()


def idempotent_replay(
    session: Session, institution_id: UUID, key: str, fingerprint: str
) -> UploadResponse | None:
    """Original response for a repeated key; 409 if the key carried other input."""
    batch = session.scalar(
        select(SubmissionBatch).where(
            SubmissionBatch.institution_id == institution_id,
            SubmissionBatch.idempotency_key == key,
        )
    )
    if batch is None:
        return None
    if batch.idempotency_fingerprint != fingerprint:
        raise APIError(
            409,
            "IDEMPOTENCY_KEY_REUSED",
            "Idempotency key used with a different upload",
        )
    # Only batches received no later than the original count, so the body is stable.
    earlier = session.scalar(
        select(SubmissionBatch.id)
        .where(
            SubmissionBatch.scope_id == batch.scope_id,
            SubmissionBatch.file_sha256 == batch.file_sha256,
            SubmissionBatch.id != batch.id,
            SubmissionBatch.received_at <= batch.received_at,
        )
        .limit(1)
    )
    return UploadResponse(
        id=batch.id, warnings=["DUPLICATE_UPLOAD"] if earlier is not None else []
    )


def persist_candidate(
    session: Session,
    user: User,
    context: UploadContext,
    data: bytes,
    filename: str,
    rows: list[ParsedRow],
    deadline: float,
    source: str = "CSV_UPLOAD",
    idempotency: tuple[str, str] | None = None,
) -> UploadResponse:
    """`idempotency` is an optional (key, fingerprint) pair."""
    try:
        upload_scope(session, user, context)
        check_budget(deadline)
        scope_values = {
            "institution_id": context.institution_id,
            "programme_id": context.programme_id,
            "academic_year": context.academic_year,
        }
        session.execute(
            insert(SubmissionScope)
            .values(**scope_values)
            .on_conflict_do_nothing(constraint="uq_submission_scope")
        )
        scope = session.scalar(
            select(SubmissionScope).where(
                SubmissionScope.institution_id == context.institution_id,
                SubmissionScope.programme_id == context.programme_id,
                SubmissionScope.academic_year == context.academic_year,
            )
        )
        assert scope is not None
        batch = SubmissionBatch(
            scope_id=scope.id,
            institution_id=context.institution_id,
            programme_id=context.programme_id,
            academic_year=context.academic_year,
            uploaded_by=user.id,
            filename=filename,
            file_sha256=sha256(data).hexdigest(),
            file_size_bytes=len(data),
            row_count=len(rows),
            source=source,
            idempotency_key=idempotency[0] if idempotency else None,
            idempotency_fingerprint=idempotency[1] if idempotency else None,
            schema_version=context.schema_version,
            submission_mode="SNAPSHOT",
            status=ProcessingStatus.PROCESSING,
            base_batch_id=scope.current_batch_id,
            base_scope_revision=scope.revision,
        )
        session.add(batch)
        session.flush()
        for row in rows:
            check_budget(deadline)
            values = row.normalized
            session.add(
                StudentRecordVersion(
                    batch_id=batch.id,
                    source_row_number=row.number,
                    institution_id=context.institution_id,
                    programme_id=context.programme_id,
                    academic_year=context.academic_year,
                    college_student_id=values["college_student_id"],
                    full_name_demo=values["student_name"],
                    apaar_identifier_encrypted_or_demo_token=values["apaar_id"],
                    apaar_match_hash=None,
                    admission_category=values["admission_category"],
                    enrollment_status=values["enrollment_status"],
                    enrollment_date=row.enrollment_date,
                    original_json=row.original,
                    normalized_json=values,
                )
            )
        record_action(
            session,
            actor_id=user.id,
            institution_id=context.institution_id,
            action="SUBMISSION_UPLOADED",
            entity_type="submission_batches",
            entity_id=batch.id,
        )
        batch.status = ProcessingStatus.COMPLETED
        batch.completed_at = datetime.now(UTC)
        session.flush()
        duplicate = session.scalar(
            select(SubmissionBatch.id)
            .where(
                SubmissionBatch.scope_id == scope.id,
                SubmissionBatch.file_sha256 == batch.file_sha256,
                SubmissionBatch.id != batch.id,
            )
            .limit(1)
        )
        result = UploadResponse(
            id=batch.id, warnings=["DUPLICATE_UPLOAD"] if duplicate is not None else []
        )
        check_budget(deadline)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise


def scoped_batch(session: Session, user: User, batch_id: UUID) -> SubmissionBatch:
    require_submission_role(user)
    statement = select(SubmissionBatch).where(SubmissionBatch.id == batch_id)
    if user.role == Role.INSTITUTION_ADMIN:
        statement = statement.where(
            SubmissionBatch.institution_id == user.institution_id
        )
    batch = session.scalar(statement)
    if batch is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return batch


def describe_batches(
    session: Session, items: list[BatchResponse]
) -> list[BatchResponse]:
    if not items:
        return items
    scope_ids = {item.scope_id for item in items}
    current = {
        scope_id: batch_id
        for scope_id, batch_id in session.execute(
            select(SubmissionScope.id, SubmissionScope.current_batch_id).where(
                SubmissionScope.id.in_(scope_ids)
            )
        ).all()
    }
    duplicates = {
        (scope_id, digest)
        for scope_id, digest in session.execute(
            select(SubmissionBatch.scope_id, SubmissionBatch.file_sha256)
            .where(SubmissionBatch.scope_id.in_(scope_ids))
            .group_by(SubmissionBatch.scope_id, SubmissionBatch.file_sha256)
            .having(func.count() > 1)
        ).all()
    }
    for item in items:
        item.is_current = current[item.scope_id] == item.id
        item.snapshot_state = (
            "CURRENT"
            if item.is_current
            else "PREVIOUS"
            if item.activated_at
            else "CANDIDATE"
        )
        item.warnings = (
            ["DUPLICATE_UPLOAD"]
            if (item.scope_id, item.file_sha256) in duplicates
            else []
        )
    # Import at the integration boundary: validation consumes submission helpers.
    from app.modules.submissions.activation import eligibility
    from app.modules.submissions.models import SubmissionReview
    from app.modules.validation.services import run_response, selected_run

    for item in items:
        run = selected_run(session, item.id)
        batch = session.get(SubmissionBatch, item.id)
        assert batch is not None
        item.activation_eligibility = eligibility(session, batch, run)
        if batch.activation_review_id:
            receipt = session.get(SubmissionReview, batch.activation_review_id)
            assert receipt is not None
            item.activation_provenance = {
                "review_id": str(receipt.id),
                "validation_run_id": str(receipt.validation_run_id),
                "activated_by": str(receipt.reviewed_by),
                "previous_batch_id": str(receipt.expected_current_batch_id)
                if receipt.expected_current_batch_id
                else None,
                "scope_revision": receipt.expected_scope_revision + 1,
            }
        if run is not None:
            description = run_response(session, run)
            item.validation_performed = True
            item.latest_validation_run_id = run.id
            item.validation_summary = {
                "record_status_counts": run.summary_json["record_status_counts"],
                "finding_count": run.summary_json["finding_count"],
                "cross_current_freshness": description.cross_current_freshness,
                "matching_assessment": run.summary_json["matching_assessment"],
                "current_overlap_records": description.current_overlap_records,
            }
    return items


def row_response(row: StudentRecordVersion) -> RowResponse:
    token = row.apaar_identifier_encrypted_or_demo_token
    masked = (
        "*" * len(token) if len(token) <= 4 else "*" * (len(token) - 4) + token[-4:]
    )
    # Explicit fields prevent accidentally exposing stored original/normalized JSON.
    return RowResponse(
        id=row.id,
        batch_id=row.batch_id,
        source_row_number=row.source_row_number,
        college_student_id=row.college_student_id,
        student_name=row.full_name_demo,
        academic_year=row.normalized_json["academic_year"],
        programme_code=row.normalized_json["programme_code"],
        admission_category=row.admission_category,
        enrollment_status=row.enrollment_status,
        enrollment_date=row.enrollment_date,
        apaar_id_masked=masked,
    )
