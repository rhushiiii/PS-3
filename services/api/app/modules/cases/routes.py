from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.core.http import AppSettings, error_responses, no_store
from app.core.pagination import Page, PageNumber, PageSize
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

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Officer cases"],
    responses=error_responses(401, 403, 404, 409, 422, 500, 503),
)


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
    no_store(response)
    return list_cases(session, user, filters, settings, page, page_size)


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
