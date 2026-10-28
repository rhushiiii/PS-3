from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.core.config import Settings
from app.core.http import ErrorResponse
from app.core.pagination import Page, Pagination
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.submissions.routes import PageNumber, PageSize, no_store
from app.modules.verification.schemas import VerificationRequest, VerificationResponse
from app.modules.verification.services import (
    request_verification,
    scoped_record,
    verification_history,
    verification_response,
)

router = APIRouter(
    prefix="/api/v1/records",
    tags=["APAAR verification"],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 500, 503)
    },
)


@router.post(
    "/{record_version_id}/apaar-verify",
    response_model=VerificationResponse,
    status_code=201,
)
def verify(
    record_version_id: UUID,
    body: VerificationRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> VerificationResponse:
    result = request_verification(
        session,
        user,
        record_version_id,
        body.purpose,
        body.consent_ref,
        cast(Settings, request.app.state.settings),
    )
    no_store(response)
    return result


@router.get(
    "/{record_version_id}/apaar-verify",
    response_model=Page[VerificationResponse],
)
def history(
    record_version_id: UUID,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[VerificationResponse]:
    scoped_record(session, user, record_version_id)
    items = verification_history(session, record_version_id)
    no_store(response)
    selected = items[(page - 1) * page_size : page * page_size]
    return Page[VerificationResponse](
        data=[verification_response(item) for item in selected],
        pagination=Pagination(page=page, page_size=page_size, total=len(items)),
    )
