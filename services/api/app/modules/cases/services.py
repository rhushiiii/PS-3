from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import Role, User
from app.modules.cases.models import CaseEvent, CaseRecord, ReviewCase
from app.modules.cases.schemas import (
    CaseActionRequest,
    CaseCreateRequest,
    CaseEventResponse,
    CaseResponse,
    CaseStatus,
)
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch

ACTIONS_BY_STATUS: dict[str, set[str]] = {
    "OPEN": {"COMMENT", "REQUEST_CORRECTION", "ASSIGNED", "RESOLVED"},
    "UNDER_REVIEW": {"COMMENT", "REQUEST_CORRECTION", "ASSIGNED", "RESOLVED"},
    "AWAITING_CORRECTION": {"COMMENT", "ASSIGNED"},
    "RESOLVED": {"COMMENT", "CLOSED"},
    "CLOSED": set(),
}
NEXT_STATUS: dict[str, str] = {
    "REQUEST_CORRECTION": "AWAITING_CORRECTION",
    "RESOLVED": "RESOLVED",
    "CLOSED": "CLOSED",
}


def require_case_role(user: User, *, writing: bool = False) -> None:
    allowed = (
        {Role.AICTE_OFFICER}
        if writing
        else {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER}
    )
    if user.role not in allowed:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")


def scoped_case(session: Session, user: User, case_id: UUID) -> ReviewCase:
    require_case_role(user)
    case = session.get(ReviewCase, case_id)
    if case is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    if user.role == Role.INSTITUTION_ADMIN and case.institution_id != (
        user.institution_id
    ):
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return case


def case_response(session: Session, case: ReviewCase) -> CaseResponse:
    record_ids = [
        row.record_version_id
        for row in session.scalars(
            select(CaseRecord)
            .where(CaseRecord.case_id == case.id)
            .order_by(CaseRecord.linked_at, CaseRecord.id)
        )
    ]
    events = [
        CaseEventResponse(
            id=event.id,
            case_id=event.case_id,
            actor_id=event.actor_id,
            action=event.action,
            comment=event.comment,
            linked_batch_id=event.linked_batch_id,
            created_at=event.created_at,
        )
        for event in session.scalars(
            select(CaseEvent)
            .where(CaseEvent.case_id == case.id)
            .order_by(CaseEvent.ordinal)
        )
    ]
    return CaseResponse(
        id=case.id,
        institution_id=case.institution_id,
        opened_by=case.opened_by,
        assigned_to=case.assigned_to,
        status=case.status,
        category=case.category,
        summary=case.summary,
        opened_at=case.opened_at,
        resolved_at=case.resolved_at,
        record_version_ids=record_ids,
        events=events,
    )


def open_case(session: Session, user: User, body: CaseCreateRequest) -> CaseResponse:
    require_case_role(user, writing=True)
    unique_ids = list(dict.fromkeys(body.record_version_ids))
    records = list(
        session.scalars(
            select(StudentRecordVersion).where(StudentRecordVersion.id.in_(unique_ids))
        )
    )
    if len(records) != len(unique_ids):
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    institution_ids = {record.institution_id for record in records}
    if len(institution_ids) != 1:
        raise APIError(
            422,
            "INVALID_REQUEST",
            "A case must reference a single institution's records",
        )
    institution_id = institution_ids.pop()
    opened_at = datetime.now(UTC)
    case = ReviewCase(
        id=uuid4(),
        institution_id=institution_id,
        opened_by=user.id,
        status="OPEN",
        category=body.category,
        summary=body.summary,
        opened_at=opened_at,
    )
    session.add(case)
    session.flush()
    for record in records:
        session.add(
            CaseRecord(
                id=uuid4(),
                case_id=case.id,
                record_version_id=record.id,
                batch_id=record.batch_id,
                linked_by=user.id,
            )
        )
    session.add(
        CaseEvent(
            id=uuid4(),
            case_id=case.id,
            actor_id=user.id,
            action="OPENED",
            comment=body.summary,
        )
    )
    record_action(
        session,
        actor_id=user.id,
        institution_id=institution_id,
        action="CASE_OPENED",
        entity_type="review_cases",
        entity_id=case.id,
    )
    session.flush()
    result = case_response(session, case)
    session.commit()
    return result


def apply_action(
    session: Session, user: User, case_id: UUID, body: CaseActionRequest
) -> CaseResponse:
    case = scoped_case(session, user, case_id)
    if user.role == Role.INSTITUTION_ADMIN and body.action != "COMMENT":
        raise APIError(403, "FORBIDDEN_ROLE", "Institutions may only comment")
    if body.action not in ACTIONS_BY_STATUS.get(case.status, set()):
        raise APIError(
            409,
            "INVALID_CASE_TRANSITION",
            f"Cannot apply {body.action} to a case in status {case.status}",
        )
    if body.action == "ASSIGNED":
        if body.assigned_to is None:
            raise APIError(422, "INVALID_REQUEST", "assigned_to is required")
        case.assigned_to = body.assigned_to
    new_status = NEXT_STATUS.get(body.action)
    if new_status is not None:
        case.status = new_status
        if new_status == "RESOLVED":
            case.resolved_at = datetime.now(UTC)
    session.add(
        CaseEvent(
            id=uuid4(),
            case_id=case.id,
            actor_id=user.id,
            action=body.action,
            comment=body.comment,
        )
    )
    record_action(
        session,
        actor_id=user.id,
        institution_id=case.institution_id,
        action=f"CASE_{body.action}",
        entity_type="review_cases",
        entity_id=case.id,
    )
    session.flush()
    result = case_response(session, case)
    session.commit()
    return result


def list_cases(
    session: Session,
    user: User,
    status: CaseStatus | None,
    page: int,
    page_size: int,
) -> tuple[list[ReviewCase], int]:
    require_case_role(user)
    statement = select(ReviewCase)
    if user.role == Role.INSTITUTION_ADMIN:
        statement = statement.where(ReviewCase.institution_id == user.institution_id)
    if status is not None:
        statement = statement.where(ReviewCase.status == status)
    total = (
        session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        or 0
    )
    items = list(
        session.scalars(
            statement.order_by(ReviewCase.opened_at.desc(), ReviewCase.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


def record_correction_received(session: Session, batch: SubmissionBatch) -> None:
    """Advisory-only: never blocks or alters the upload/activation path."""
    for case in session.scalars(
        select(ReviewCase).where(
            ReviewCase.institution_id == batch.institution_id,
            ReviewCase.status == "AWAITING_CORRECTION",
        )
    ):
        case.status = "UNDER_REVIEW"
        session.add(
            CaseEvent(
                id=uuid4(),
                case_id=case.id,
                actor_id=None,
                action="CORRECTION_RECEIVED",
                comment=None,
                linked_batch_id=batch.id,
            )
        )
