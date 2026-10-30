from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime

from app.core.http import APIError, error_responses, no_store
from app.core.pagination import Page, PageNumber, PageSize
from app.modules.audit import services
from app.modules.audit.schemas import (
    AuditActionsResponse,
    AuditEventResponse,
    AuditFilters,
)
from app.modules.auth.dependencies import CurrentUser, DatabaseSession, require_roles
from app.modules.auth.models import Role, User

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit explorer"],
    responses=error_responses(401, 403, 404, 422, 503),
)


def audit_reader(user: CurrentUser) -> User:
    # Officers only: managers and institution admins see no audit trail here.
    require_roles(user, {Role.AICTE_OFFICER})
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
    page: PageNumber = 1,
    page_size: PageSize = 25,
) -> Page[AuditEventResponse]:
    if occurred_from and occurred_to and occurred_from > occurred_to:
        raise APIError(422, "INVALID_REQUEST", "from must not be after to")
    no_store(response)
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
    no_store(response)
    return AuditActionsResponse(data=services.list_actions(session))


@router.get("/events/{event_id}", response_model=AuditEventResponse)
def event(
    event_id: UUID, response: Response, _: Officer, session: DatabaseSession
) -> AuditEventResponse:
    no_store(response)
    return services.get_event(session, event_id)
