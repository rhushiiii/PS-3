"""In-app notifications.

Rows are created inside the caller's transaction (the same one that records the
case action), so a notification exists if and only if the action committed.
`notify` is the single creation point: an email/SMS adapter would plug in here,
fanning out the same title/body after commit. None exists yet.

Text is deliberately generic (short case id, institution name, status): never
student names, college IDs or APAAR values.
"""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.http import not_found
from app.core.pagination import Page, paginate
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import Role, User
from app.modules.cases.models import CLOSED_STATUSES, ReviewCase
from app.modules.institutions.models import Institution
from app.modules.notifications.models import Notification, NotificationKind
from app.modules.notifications.schemas import NotificationResponse

TITLES: dict[str, str] = {
    "CASE_ASSIGNED": "Case assigned to you",
    "CORRECTION_REQUESTED": "Correction requested",
    "RESPONSE_SUBMITTED": "Institution response received",
    "CASE_RESOLVED": "Case resolved",
    "CASE_REJECTED": "Case rejected",
    "CASE_CLOSED": "Case closed",
    "CASE_OVERDUE": "Case overdue",
}
OVERDUE_BATCH_LIMIT = 200


def require_notification_role(user: User) -> None:
    # Same audience as cases; managers have no case notifications.
    require_roles(user, {Role.INSTITUTION_ADMIN, Role.AICTE_OFFICER})


def active_user_ids(
    session: Session, role: Role, institution_id: UUID | None = None
) -> list[UUID]:
    statement = select(User.id).where(User.role == role, User.active.is_(True))
    if institution_id is not None:
        statement = statement.where(User.institution_id == institution_id)
    return list(session.scalars(statement.order_by(User.id)))


def institution_admin_ids(session: Session, case: ReviewCase) -> list[UUID]:
    return active_user_ids(session, Role.INSTITUTION_ADMIN, case.institution_id)


def officer_recipient_ids(session: Session, case: ReviewCase) -> list[UUID]:
    """The assignee when active, otherwise every active officer."""
    officers = active_user_ids(session, Role.AICTE_OFFICER)
    if case.assigned_to is not None and case.assigned_to in officers:
        return [case.assigned_to]
    return officers


def notify(
    session: Session,
    recipient_ids: Iterable[UUID],
    kind: NotificationKind,
    case: ReviewCase,
    *,
    dedupe_key: str | None = None,
) -> None:
    recipients = list(dict.fromkeys(recipient_ids))
    if not recipients:
        return
    institution = session.get(Institution, case.institution_id)
    name = institution.name if institution is not None else "institution"
    short_id = str(case.id)[:8]
    session.execute(
        insert(Notification)
        .values(
            [
                {
                    "id": uuid4(),
                    "recipient_user_id": recipient,
                    "institution_id": case.institution_id,
                    "kind": kind,
                    "case_id": case.id,
                    "title": f"{TITLES[kind]}: {short_id}",
                    "body": f"Case {short_id} for {name} is {case.status}.",
                    "dedupe_key": dedupe_key,
                }
                for recipient in recipients
            ]
        )
        .on_conflict_do_nothing()
    )


def ensure_overdue_notifications(session: Session, user: User) -> None:
    """Lazy and idempotent: no scheduler, one row per recipient/case/due date."""
    if user.role != Role.AICTE_OFFICER:
        return
    cases = session.scalars(
        select(ReviewCase)
        .where(
            ReviewCase.due_at < datetime.now(UTC),
            ReviewCase.status.not_in(CLOSED_STATUSES),
            (ReviewCase.assigned_to == user.id) | ReviewCase.assigned_to.is_(None),
        )
        .order_by(ReviewCase.due_at)
        .limit(OVERDUE_BATCH_LIMIT)
    )
    for case in cases:
        assert case.due_at is not None
        notify(
            session,
            [user.id],
            "CASE_OVERDUE",
            case,
            dedupe_key=f"overdue:{case.id}:{case.due_at.isoformat()}",
        )


def list_notifications(
    session: Session, user: User, unread: bool, page: int, page_size: int
) -> Page[NotificationResponse]:
    require_notification_role(user)
    ensure_overdue_notifications(session, user)
    session.commit()
    statement = select(Notification).where(Notification.recipient_user_id == user.id)
    if unread:
        statement = statement.where(Notification.read_at.is_(None))
    return paginate(
        session,
        statement.order_by(Notification.created_at.desc(), Notification.id.desc()),
        NotificationResponse,
        page,
        page_size,
    )


def unread_count(session: Session, user: User) -> int:
    require_notification_role(user)
    ensure_overdue_notifications(session, user)
    session.commit()
    return (
        session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_user_id == user.id)
            .where(Notification.read_at.is_(None))
        )
        or 0
    )


def mark_read(
    session: Session, user: User, notification_id: UUID
) -> NotificationResponse:
    require_notification_role(user)
    notification = session.get(Notification, notification_id)
    if notification is None or notification.recipient_user_id != user.id:
        raise not_found()
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
    result = NotificationResponse.model_validate(notification)
    session.commit()
    return result


def mark_all_read(session: Session, user: User) -> int:
    require_notification_role(user)
    result = session.execute(
        update(Notification)
        .where(Notification.recipient_user_id == user.id)
        .where(Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    updated = cast(CursorResult[Any], result).rowcount
    session.commit()
    return updated
