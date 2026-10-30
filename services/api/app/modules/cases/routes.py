from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.config import Settings
from app.core.http import ErrorResponse
from app.core.pagination import Page, Pagination
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.cases.models import CasePriority, CaseSeverity, CaseStatus
from app.modules.cases.schemas import (
    AssigneeResponse,
    CaseActionRequest,
    CaseCreateRequest,
    CaseResponse,
)
from app.modules.cases.services import (
    CaseFilters,
    apply_action,
    case_response,
    list_assignees,
    list_cases,
    open_case,
    scoped_case,
)
from app.modules.submissions.routes import PageNumber, PageSize, no_store

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Officer cases"],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 500, 503)
    },
)


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post(
    "",
    response_model=CaseResponse,
    status_code=201,
    dependencies=[rate_limit("cases")],
)
def create(
    body: CaseCreateRequest,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> CaseResponse:
    result = open_case(session, user, body, settings)
    no_store(response)
    return result


@router.get("", response_model=Page[CaseResponse])
def list_(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
    institution_id: UUID | None = None,
    status: CaseStatus | None = None,
    severity: CaseSeverity | None = None,
    priority: CasePriority | None = None,
    programme_id: UUID | None = None,
    assigned_to: UUID | None = None,
    overdue: bool | None = None,
    min_age_days: Annotated[int | None, Query(ge=0, le=3650)] = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[CaseResponse]:
    filters = CaseFilters(
        institution_id=institution_id,
        status=status,
        severity=severity,
        priority=priority,
        programme_id=programme_id,
        assigned_to=assigned_to,
        overdue=overdue,
        min_age_days=min_age_days,
    )
    items, total = list_cases(session, user, filters, page, page_size)
    no_store(response)
    return Page[CaseResponse](
        data=[case_response(session, item, settings) for item in items],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.get("/assignees", response_model=list[AssigneeResponse])
def assignees(
    response: Response, user: CurrentUser, session: DatabaseSession
) -> list[AssigneeResponse]:
    result = list_assignees(session, user)
    no_store(response)
    return result


@router.get("/{case_id}", response_model=CaseResponse)
def detail(
    case_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> CaseResponse:
    case = scoped_case(session, user, case_id)
    no_store(response)
    return case_response(session, case, settings)


@router.post(
    "/{case_id}/actions",
    response_model=CaseResponse,
    status_code=201,
    dependencies=[rate_limit("cases")],
)
def act(
    case_id: UUID,
    body: CaseActionRequest,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> CaseResponse:
    result = apply_action(session, user, case_id, body, settings)
    no_store(response)
    return result
