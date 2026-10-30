from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, exists, not_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError, not_found
from app.core.pagination import count_rows, window
from app.modules.audit.services import record_action
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import Role, User
from app.modules.cases.models import (
    CLOSED_STATUSES,
    CaseEvent,
    CasePriority,
    CaseRecord,
    CaseSeverity,
    CaseStatus,
    ReviewCase,
)
from app.modules.cases.schemas import (
    AssigneeResponse,
    CaseActionRequest,
    CaseCreateRequest,
    CaseEventResponse,
    CaseResponse,
)
from app.modules.notifications.models import NotificationKind
from app.modules.notifications.services import (
    institution_admin_ids,
    notify,
    officer_recipient_ids,
)
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch

NON_TERMINAL = {
    "OPEN",
    "ASSIGNED",
    "UNDER_REVIEW",
    "AWAITING_CORRECTION",
    "RESPONSE_SUBMITTED",
}
# Valid actions per status. UPDATED (priority/severity/due date) is added for
# every non-terminal status below.
ACTIONS_BY_STATUS: dict[str, set[str]] = {
    "OPEN": {"COMMENT", "ASSIGNED", "START_REVIEW", "REQUEST_CORRECTION"},
    "ASSIGNED": {"COMMENT", "ASSIGNED", "START_REVIEW", "REQUEST_CORRECTION"},
    "UNDER_REVIEW": {
        "COMMENT",
        "ASSIGNED",
        "REQUEST_CORRECTION",
        "RESOLVED",
        "REJECTED",
    },
    "AWAITING_CORRECTION": {"COMMENT", "ASSIGNED", "RESPONSE_SUBMITTED"},
    "RESPONSE_SUBMITTED": {
        "COMMENT",
        "ASSIGNED",
        "START_REVIEW",
        "REQUEST_CORRECTION",
    },
    "RESOLVED": {"COMMENT", "CLOSED"},
    "REJECTED": {"COMMENT", "CLOSED"},
    "CLOSED": set(),
}
for _status in NON_TERMINAL:
    ACTIONS_BY_STATUS[_status].add("UPDATED")
NEXT_STATUS: dict[str, str] = {
    "START_REVIEW": "UNDER_REVIEW",
    "REQUEST_CORRECTION": "AWAITING_CORRECTION",
    "RESPONSE_SUBMITTED": "RESPONSE_SUBMITTED",
    "RESOLVED": "RESOLVED",
    "REJECTED": "REJECTED",
    "CLOSED": "CLOSED",
}
NOTIFICATION_FOR_ACTION: dict[str, NotificationKind] = {
    "RESOLVED": "CASE_RESOLVED",
    "REJECTED": "CASE_REJECTED",
    "CLOSED": "CASE_CLOSED",
}


@dataclass(frozen=True)
class CaseFilters:
    institution_id: UUID | None = None
    status: CaseStatus | None = None
    severity: CaseSeverity | None = None
    priority: CasePriority | None = None
    programme_id: UUID | None = None
    assigned_to: UUID | None = None
    overdue: bool | None = None
    min_age_days: int | None = None


def require_case_role(user: User, *, writing: bool = False) -> None:
    allowed = (
        {Role.AICTE_OFFICER}
        if writing
        else {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER}
    )
    require_roles(user, allowed)


def scoped_case(session: Session, user: User, case_id: UUID) -> ReviewCase:
    require_case_role(user)
    case = session.get(ReviewCase, case_id)
    if case is None:
        raise not_found()
    if user.role == Role.INSTITUTION_ADMIN and case.institution_id != (
        user.institution_id
    ):
        raise not_found()
    return case


def case_flags(
    case: ReviewCase, settings: Settings, now: datetime
) -> tuple[bool, bool, int]:
    """Computed at read time (no worker): overdue, escalated, age in days."""
    overdue = (
        case.due_at is not None
        and case.due_at < now
        and case.status not in CLOSED_STATUSES
    )
    escalated = (
        overdue
        and case.due_at is not None
        and now - case.due_at
        >= timedelta(days=settings.case_escalation_after_days_overdue)
    )
    return overdue, escalated, max(0, (now - case.opened_at).days)


def case_response(
    session: Session, case: ReviewCase, settings: Settings
) -> CaseResponse:
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
    overdue, escalated, age_days = case_flags(case, settings, datetime.now(UTC))
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
        priority=case.priority,
        severity=case.severity,
        due_at=case.due_at,
        resolution_reason=case.resolution_reason,
        is_overdue=overdue,
        is_escalated=escalated,
        age_days=age_days,
        record_version_ids=record_ids,
        events=events,
    )


def open_case(
    session: Session, user: User, body: CaseCreateRequest, settings: Settings
) -> CaseResponse:
    require_case_role(user, writing=True)
    unique_ids = list(dict.fromkeys(body.record_version_ids))
    records = list(
        session.scalars(
            select(StudentRecordVersion).where(StudentRecordVersion.id.in_(unique_ids))
        )
    )
    if len(records) != len(unique_ids):
        raise not_found()
    institution_ids = {record.institution_id for record in records}
    if len(institution_ids) != 1:
        raise APIError(
            422,
            "INVALID_REQUEST",
            "A case must reference a single institution's records",
        )
    institution_id = institution_ids.pop()
    opened_at = datetime.now(UTC)
    due_days = settings.case_due_days_by_priority[body.priority]
    case = ReviewCase(
        id=uuid4(),
        institution_id=institution_id,
        opened_by=user.id,
        status="OPEN",
        category=body.category,
        summary=body.summary,
        opened_at=opened_at,
        priority=body.priority,
        severity=body.severity,
        due_at=body.due_at or opened_at + timedelta(days=due_days),
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
    result = case_response(session, case, settings)
    session.commit()
    return result


def validated_assignee(session: Session, user_id: UUID) -> User:
    assignee = session.get(User, user_id)
    if assignee is None or not assignee.active or assignee.role != Role.AICTE_OFFICER:
        raise APIError(422, "INVALID_REQUEST", "assigned_to must be an active officer")
    return assignee


def shown(value: object) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def apply_update(case: ReviewCase, body: CaseActionRequest) -> str:
    """Apply priority/severity/due_at changes; return a PII-free change note."""
    changes: list[str] = []
    for field in ("priority", "severity", "due_at"):
        new = getattr(body, field)
        old = getattr(case, field)
        if new is not None and new != old:
            setattr(case, field, new)
            changes.append(f"{field}: {shown(old)} -> {shown(new)}")
    if not changes:
        raise APIError(422, "INVALID_REQUEST", "No changes requested")
    return "; ".join(changes)


def apply_action(
    session: Session,
    user: User,
    case_id: UUID,
    body: CaseActionRequest,
    settings: Settings,
) -> CaseResponse:
    case = scoped_case(session, user, case_id)
    if user.role == Role.INSTITUTION_ADMIN:
        if body.action not in {"COMMENT", "RESPONSE_SUBMITTED"}:
            raise APIError(
                403, "FORBIDDEN_ROLE", "Institutions may only comment or respond"
            )
    elif body.action == "RESPONSE_SUBMITTED":
        raise APIError(403, "FORBIDDEN_ROLE", "Only the institution may respond")
    if body.action not in ACTIONS_BY_STATUS.get(case.status, set()):
        raise APIError(
            409,
            "INVALID_CASE_TRANSITION",
            f"Cannot apply {body.action} to a case in status {case.status}",
        )
    comment = body.comment
    if body.action == "ASSIGNED":
        assert body.assigned_to is not None
        case.assigned_to = validated_assignee(session, body.assigned_to).id
        if case.status in {"OPEN", "ASSIGNED"}:
            case.status = "ASSIGNED"
    elif body.action == "UPDATED":
        note = apply_update(case, body)
        comment = f"{note}\n{comment}" if comment else note
    elif body.action in {"RESOLVED", "REJECTED"}:
        case.resolution_reason = (body.resolution_reason or "").strip()
        case.resolved_at = datetime.now(UTC)
    new_status = NEXT_STATUS.get(body.action)
    if new_status is not None:
        case.status = new_status
    session.add(
        CaseEvent(
            id=uuid4(),
            case_id=case.id,
            actor_id=user.id,
            action=body.action,
            comment=comment,
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
    notify_for_action(session, case, body)
    session.flush()
    result = case_response(session, case, settings)
    session.commit()
    return result


def notify_for_action(
    session: Session, case: ReviewCase, body: CaseActionRequest
) -> None:
    if body.action == "ASSIGNED" and case.assigned_to is not None:
        notify(session, [case.assigned_to], "CASE_ASSIGNED", case)
    elif body.action == "REQUEST_CORRECTION":
        notify(
            session, institution_admin_ids(session, case), "CORRECTION_REQUESTED", case
        )
    elif body.action == "RESPONSE_SUBMITTED":
        notify(
            session, officer_recipient_ids(session, case), "RESPONSE_SUBMITTED", case
        )
    elif body.action in NOTIFICATION_FOR_ACTION:
        kind = NOTIFICATION_FOR_ACTION[body.action]
        notify(session, institution_admin_ids(session, case), kind, case)


def list_assignees(session: Session, user: User) -> list[AssigneeResponse]:
    require_roles(user, {Role.AICTE_OFFICER})
    # Emails are deliberately not exposed; fall back to a short opaque label.
    return [
        AssigneeResponse(
            id=officer.id,
            display_name=officer.demo_alias or f"Officer {str(officer.id)[:8]}",
        )
        for officer in session.scalars(
            select(User)
            .where(User.role == Role.AICTE_OFFICER, User.active.is_(True))
            .order_by(User.demo_alias, User.id)
        )
    ]


def list_cases(
    session: Session,
    user: User,
    filters: CaseFilters,
    page: int,
    page_size: int,
) -> tuple[list[ReviewCase], int]:
    require_case_role(user)
    now = datetime.now(UTC)
    statement = select(ReviewCase)
    if user.role == Role.INSTITUTION_ADMIN:
        statement = statement.where(ReviewCase.institution_id == user.institution_id)
    # An admin asking for another institution simply matches nothing (no leak).
    equality = (
        (ReviewCase.institution_id, filters.institution_id),
        (ReviewCase.status, filters.status),
        (ReviewCase.severity, filters.severity),
        (ReviewCase.priority, filters.priority),
        (ReviewCase.assigned_to, filters.assigned_to),
    )
    for column, value in equality:
        if value is not None:
            statement = statement.where(column == value)
    if filters.programme_id is not None:
        statement = statement.where(
            exists().where(
                CaseRecord.case_id == ReviewCase.id,
                StudentRecordVersion.id == CaseRecord.record_version_id,
                StudentRecordVersion.programme_id == filters.programme_id,
            )
        )
    if filters.overdue is not None:
        is_overdue = and_(
            ReviewCase.due_at.is_not(None),
            ReviewCase.due_at < now,
            ReviewCase.status.not_in(CLOSED_STATUSES),
        )
        statement = statement.where(is_overdue if filters.overdue else not_(is_overdue))
    if filters.min_age_days is not None:
        statement = statement.where(
            ReviewCase.opened_at <= now - timedelta(days=filters.min_age_days)
        )
    total = count_rows(session, statement)
    ordered = statement.order_by(ReviewCase.opened_at.desc(), ReviewCase.id.desc())
    return list(session.scalars(window(ordered, page, page_size))), total


def record_correction_received(session: Session, batch: SubmissionBatch) -> None:
    """Advisory-only: never blocks or alters the upload/activation path."""
    awaiting = list(
        session.scalars(
            select(ReviewCase).where(
                ReviewCase.institution_id == batch.institution_id,
                ReviewCase.status == "AWAITING_CORRECTION",
            )
        )
    )
    for case in awaiting:
        case.status = "RESPONSE_SUBMITTED"
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
        notify(
            session, officer_recipient_ids(session, case), "RESPONSE_SUBMITTED", case
        )
