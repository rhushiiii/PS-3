from uuid import UUID

from fastapi import APIRouter, Response

from app.core.http import ErrorResponse
from app.core.pagination import Page, Pagination
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.cases.schemas import (
    CaseActionRequest,
    CaseCreateRequest,
    CaseResponse,
    CaseStatus,
)
from app.modules.cases.services import (
    apply_action,
    case_response,
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


@router.post("", response_model=CaseResponse, status_code=201)
def create(
    body: CaseCreateRequest,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> CaseResponse:
    result = open_case(session, user, body)
    no_store(response)
    return result


@router.get("", response_model=Page[CaseResponse])
def list_(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    status: CaseStatus | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[CaseResponse]:
    items, total = list_cases(session, user, status, page, page_size)
    no_store(response)
    return Page[CaseResponse](
        data=[case_response(session, item) for item in items],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.get("/{case_id}", response_model=CaseResponse)
def detail(
    case_id: UUID, response: Response, user: CurrentUser, session: DatabaseSession
) -> CaseResponse:
    case = scoped_case(session, user, case_id)
    no_store(response)
    return case_response(session, case)


@router.post("/{case_id}/actions", response_model=CaseResponse, status_code=201)
def act(
    case_id: UUID,
    body: CaseActionRequest,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> CaseResponse:
    result = apply_action(session, user, case_id, body)
    no_store(response)
    return result
