from uuid import UUID

from fastapi import APIRouter, Response

from app.core.http import ErrorResponse
from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.notifications.schemas import (
    NotificationResponse,
    ReadAllResponse,
    UnreadCountResponse,
)
from app.modules.notifications.services import (
    list_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)
from app.modules.submissions.routes import PageNumber, PageSize, no_store

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 422, 500, 503)
    },
)


@router.get("", response_model=Page[NotificationResponse])
def list_(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    unread: bool = False,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[NotificationResponse]:
    result = list_notifications(session, user, unread, page, page_size)
    no_store(response)
    return result


@router.get("/unread-count", response_model=UnreadCountResponse)
def count(
    response: Response, user: CurrentUser, session: DatabaseSession
) -> UnreadCountResponse:
    result = UnreadCountResponse(unread=unread_count(session, user))
    no_store(response)
    return result


@router.post("/read-all", response_model=ReadAllResponse)
def read_all(
    response: Response, user: CurrentUser, session: DatabaseSession
) -> ReadAllResponse:
    result = ReadAllResponse(marked_read=mark_all_read(session, user))
    no_store(response)
    return result


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def read(
    notification_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> NotificationResponse:
    result = mark_read(session, user, notification_id)
    no_store(response)
    return result
