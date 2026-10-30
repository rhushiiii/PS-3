from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ColumnElement, and_, false, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.core.pagination import Page, Pagination
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.cases.models import CaseRecord, ReviewCase
from app.modules.cases.services import case_flags
from app.modules.institutions.models import Institution, Programme
from app.modules.institutions.services import scoped_institution, scoped_programme
from app.modules.records.schemas import (
    FieldChange,
    HistoryEntry,
    Provenance,
    RecordDetail,
    RecordRow,
    RelatedCase,
    SnapshotState,
    VerificationSummary,
)
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.services import require_submission_role, row_response
from app.modules.validation.schemas import RecordStatus
from app.modules.validation.services import (
    finding_response,
    findings_for,
    record_statuses,
    run_response,
    selected_run,
)
from app.modules.verification.models import ApaarVerification
from app.modules.verification.services import scoped_record, verification_response

Record = StudentRecordVersion
PRESENCE_NOTE = (
    "Omission from a newer snapshot is not proof of withdrawal or transfer; "
    "enrollment status is shown as submitted."
)


def batch_state(batch: SubmissionBatch, current_batch_id: UUID | None) -> SnapshotState:
    if batch.id == current_batch_id:
        return "CURRENT"
    return "CANDIDATE" if batch.activated_at is None else "SUPERSEDED"


def to_row(
    record: Record,
    batch: SubmissionBatch,
    current_batch_id: UUID | None,
    institution_name: str,
    programme: Programme,
    status: RecordStatus | None,
) -> RecordRow:
    return RecordRow(
        record_version_id=record.id,
        institution_id=record.institution_id,
        institution_name=institution_name,
        programme_id=programme.id,
        programme_code=programme.code,
        programme_name=programme.name,
        academic_year=record.academic_year,
        college_student_id=record.college_student_id,
        student_name=record.full_name_demo,
        # The shared masking helper is the only APAAR representation exposed.
        masked_apaar=row_response(record).apaar_id_masked,
        category=record.admission_category,
        enrollment_status=record.enrollment_status,
        enrollment_date=record.enrollment_date,
        validation_status=status,
        batch_id=batch.id,
        is_current=batch.id == current_batch_id,
        snapshot_state=batch_state(batch, current_batch_id),
    )


def latest_statuses(
    session: Session, batch_ids: list[UUID]
) -> dict[UUID, dict[UUID, RecordStatus]]:
    """Per batch with a completed run: record id -> status (absent means VALID)."""
    result: dict[UUID, dict[UUID, RecordStatus]] = {}
    for batch_id in batch_ids:
        run = selected_run(session, batch_id)
        if run is not None:
            result[batch_id] = record_statuses(findings_for(session, run))
    return result


def status_clause(
    status: RecordStatus, statuses: dict[UUID, dict[UUID, RecordStatus]]
) -> ColumnElement[bool]:
    clauses = []
    for batch_id, flagged in statuses.items():
        if status == "VALID":
            clauses.append(and_(Record.batch_id == batch_id, Record.id.not_in(flagged)))
        else:
            ids = [key for key, value in flagged.items() if value == status]
            clauses.append(and_(Record.batch_id == batch_id, Record.id.in_(ids)))
    return or_(false(), *clauses)


def list_records(
    session: Session,
    user: User,
    *,
    institution_id: UUID | None,
    programme_id: UUID | None,
    academic_year: str | None,
    enrollment_status: str | None,
    validation_status: RecordStatus | None,
    q: str | None,
    include_candidates: bool,
    page: int,
    page_size: int,
) -> Page[RecordRow]:
    require_submission_role(user)
    if user.role == Role.INSTITUTION_ADMIN:
        if institution_id is not None and institution_id != user.institution_id:
            raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
        institution_id = user.institution_id
    if institution_id is not None:
        scoped_institution(session, user, institution_id)
        if programme_id is not None:
            scoped_programme(session, institution_id, programme_id)
    elif programme_id is not None and session.get(Programme, programme_id) is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")

    # Superseded snapshots are never listed; candidates only when asked for.
    visible = SubmissionBatch.id == SubmissionScope.current_batch_id
    if include_candidates:
        visible = or_(visible, SubmissionBatch.activated_at.is_(None))
    conditions = [visible]
    if institution_id is not None:
        conditions.append(Record.institution_id == institution_id)
    if programme_id is not None:
        conditions.append(Record.programme_id == programme_id)
    if academic_year is not None:
        conditions.append(Record.academic_year == academic_year)
    if enrollment_status is not None:
        conditions.append(Record.enrollment_status == enrollment_status)
    if q:
        # Student identifiers and names only; APAAR is deliberately not searchable.
        conditions.append(
            or_(
                func.lower(Record.college_student_id).startswith(
                    q.lower(), autoescape=True
                ),
                Record.full_name_demo.icontains(q, autoescape=True),
            )
        )
    source = (
        select(Record)
        .join(SubmissionBatch, SubmissionBatch.id == Record.batch_id)
        .join(SubmissionScope, SubmissionScope.id == SubmissionBatch.scope_id)
        .where(*conditions)
    )
    if validation_status is not None:
        batch_ids = list(
            session.scalars(source.with_only_columns(Record.batch_id).distinct())
        )
        statuses = latest_statuses(session, batch_ids)
        source = source.where(status_clause(validation_status, statuses))
    total = session.scalar(select(func.count()).select_from(source.subquery())) or 0
    page_rows = session.execute(
        source.with_only_columns(
            Record,
            SubmissionBatch,
            SubmissionScope.current_batch_id,
            Institution.name,
            Programme,
        )
        .join(Institution, Institution.id == Record.institution_id)
        .join(Programme, Programme.id == Record.programme_id)
        .order_by(
            Record.college_student_id,
            SubmissionBatch.received_at.desc(),
            Record.id,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    statuses = latest_statuses(session, list({row[1].id for row in page_rows}))
    data = [
        to_row(
            record,
            batch,
            current_id,
            institution_name,
            programme,
            None
            if batch.id not in statuses
            else statuses[batch.id].get(record.id, "VALID"),
        )
        for record, batch, current_id, institution_name, programme in page_rows
    ]
    return Page[RecordRow](
        data=data,
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


def record_history(
    session: Session, record: Record, current_batch_id: UUID | None
) -> list[HistoryEntry]:
    versions = session.execute(
        select(Record, SubmissionBatch)
        .join(SubmissionBatch, SubmissionBatch.id == Record.batch_id)
        .where(
            Record.institution_id == record.institution_id,
            Record.programme_id == record.programme_id,
            Record.academic_year == record.academic_year,
            Record.college_student_id == record.college_student_id,
        )
        .order_by(SubmissionBatch.received_at, Record.id)
    ).all()
    entries: list[HistoryEntry] = []
    previous: Record | None = None
    for version, batch in versions:
        changes: list[FieldChange] = []
        if previous is not None:
            for name, before, after in (
                ("student_name", previous.full_name_demo, version.full_name_demo),
                (
                    "category",
                    previous.admission_category,
                    version.admission_category,
                ),
                (
                    "enrollment_status",
                    previous.enrollment_status,
                    version.enrollment_status,
                ),
                (
                    "enrollment_date",
                    previous.enrollment_date and previous.enrollment_date.isoformat(),
                    version.enrollment_date and version.enrollment_date.isoformat(),
                ),
                (
                    "programme",
                    str(previous.programme_id),
                    str(version.programme_id),
                ),
            ):
                if before != after:
                    changes.append(
                        FieldChange(field=name, previous=before, current=after)
                    )
        entries.append(
            HistoryEntry(
                record_version_id=version.id,
                batch_id=batch.id,
                received_at=batch.received_at,
                snapshot_state=batch_state(batch, current_batch_id),
                changes=changes,
                apaar_changed=None
                if previous is None
                else previous.apaar_identifier_encrypted_or_demo_token
                != version.apaar_identifier_encrypted_or_demo_token,
            )
        )
        previous = version
    return entries


def record_detail(
    session: Session, user: User, record_version_id: UUID, settings: Settings
) -> RecordDetail:
    record = scoped_record(session, user, record_version_id)
    batch = session.get(SubmissionBatch, record.batch_id)
    scope = batch and session.get(SubmissionScope, batch.scope_id)
    institution = session.get(Institution, record.institution_id)
    programme = session.get(Programme, record.programme_id)
    assert batch and scope and institution and programme
    current_id = scope.current_batch_id
    state = batch_state(batch, current_id)

    run = selected_run(session, batch.id)
    findings = findings_for(session, run) if run else []
    statuses = record_statuses(findings)
    run_view = run_response(session, run) if run else None
    mine = [
        finding_response(finding, run_view, user)
        for finding in findings
        if run_view is not None
        and (
            finding.record_version_id == record.id
            or str(record.id)
            in finding.evidence_json_redacted.get("affected_record_ids", [])
        )
    ]

    superseded_by = (
        session.scalar(
            select(SubmissionBatch.id)
            .where(
                SubmissionBatch.scope_id == batch.scope_id,
                SubmissionBatch.activated_at > batch.activated_at,
            )
            .order_by(SubmissionBatch.activated_at)
            .limit(1)
        )
        if state == "SUPERSEDED"
        else None
    )
    presence = "NOT_APPLICABLE" if state == "CANDIDATE" else "IN_LATEST_SNAPSHOT"
    if state == "SUPERSEDED":
        in_latest = session.scalar(
            select(Record.id)
            .where(
                Record.batch_id == current_id,
                Record.college_student_id == record.college_student_id,
            )
            .limit(1)
        )
        presence = "IN_LATEST_SNAPSHOT" if in_latest else "NOT_IN_LATEST_SNAPSHOT"

    verification = session.scalar(
        select(ApaarVerification)
        .where(ApaarVerification.record_version_id == record.id)
        .order_by(ApaarVerification.requested_at.desc(), ApaarVerification.id.desc())
        .limit(1)
    )
    summary = None
    if verification is not None:
        full = verification_response(verification)
        summary = VerificationSummary(
            status=full.status,
            adapter_type=full.adapter_type,
            requested_at=full.requested_at,
            completed_at=full.completed_at,
            provenance_label=full.provenance_label,
        )

    case_query = (
        select(ReviewCase)
        .join(CaseRecord, CaseRecord.case_id == ReviewCase.id)
        .where(CaseRecord.record_version_id == record.id)
        .order_by(ReviewCase.opened_at.desc(), ReviewCase.id)
    )
    if user.role == Role.INSTITUTION_ADMIN:
        case_query = case_query.where(ReviewCase.institution_id == user.institution_id)
    now = datetime.now(UTC)
    cases = [
        RelatedCase(
            id=case.id,
            status=case.status,
            priority=case.priority,
            severity=case.severity,
            is_overdue=case_flags(case, settings, now)[0],
            opened_at=case.opened_at,
        )
        for case in session.scalars(case_query)
    ]

    row = to_row(
        record,
        batch,
        current_id,
        institution.name,
        programme,
        statuses.get(record.id, "VALID") if run else None,
    )
    result = RecordDetail(
        **row.model_dump(),
        provenance=Provenance(
            batch_id=batch.id,
            received_at=batch.received_at,
            source=batch.source,
            snapshot_state=state,
            activated_at=batch.activated_at,
            superseded_by_batch_id=superseded_by,
        ),
        snapshot_presence=presence,
        presence_note=PRESENCE_NOTE if presence == "NOT_IN_LATEST_SNAPSHOT" else None,
        findings=mine,
        verification=summary,
        cases=cases,
        history=record_history(session, record, current_id),
    )
    # Identifiers only: no APAAR, name or other record content in the audit trail.
    record_action(
        session,
        actor_id=user.id,
        institution_id=record.institution_id,
        action="RECORD_VIEWED",
        entity_type="student_record_versions",
        entity_id=record.id,
    )
    session.commit()
    return result
