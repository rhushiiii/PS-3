from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime

from app.core.http import APIError, ErrorResponse
from app.core.pagination import Page
from app.modules.audit import services
from app.modules.audit.schemas import (
    AuditActionsResponse,
    AuditEventResponse,
    AuditFilters,
)
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.auth.models import Role, User

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit explorer"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)


def audit_reader(user: CurrentUser) -> User:
    # Officers only: managers and institution admins see no audit trail here.
    if user.role != Role.AICTE_OFFICER:
        raise APIError(403, "FORBIDDEN_ROLE", "Not authorized")
    return user


Officer = Annotated[User, Depends(audit_reader)]
Short = Annotated[str | None, Query(max_length=64)]


@router.get("/events", response_model=Page[AuditEventResponse])
def events(
    response: Response,
    _: Officer,
    session: DatabaseSession,
    actor_user_id: UUID | None = None,
    action: Short = None,
    entity_type: Short = None,
    institution_id: UUID | None = None,
    occurred_from: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    occurred_to: Annotated[AwareDatetime | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[AuditEventResponse]:
    if occurred_from and occurred_to and occurred_from > occurred_to:
        raise APIError(422, "INVALID_REQUEST", "from must not be after to")
    response.headers["Cache-Control"] = "no-store"
    return services.list_events(
        session,
        AuditFilters(
            actor_user_id,
            action,
            entity_type,
            institution_id,
            occurred_from,
            occurred_to,
        ),
        page,
        page_size,
    )


@router.get("/actions", response_model=AuditActionsResponse)
def actions(
    response: Response, _: Officer, session: DatabaseSession
) -> AuditActionsResponse:
    response.headers["Cache-Control"] = "no-store"
    return AuditActionsResponse(data=services.list_actions(session))


@router.get("/events/{event_id}", response_model=AuditEventResponse)
def event(
    event_id: UUID, response: Response, _: Officer, session: DatabaseSession
) -> AuditEventResponse:
    response.headers["Cache-Control"] = "no-store"
    return services.get_event(session, event_id)
