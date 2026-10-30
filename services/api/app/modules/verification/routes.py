from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from app.core.config import Settings
from app.core.http import ErrorResponse, no_store
from app.core.idempotency import IDEMPOTENCY_KEY_PATTERN
from app.core.pagination import Page, PageNumber, PageSize, paginate_list
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.verification.schemas import (
    VerificationRequest,
    VerificationResponse,
)
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
        code: {"model": ErrorResponse}
        for code in (401, 403, 404, 409, 422, 429, 500, 503)
    },
)


@router.post(
    "/{record_version_id}/apaar-verify",
    response_model=VerificationResponse,
    status_code=201,
    dependencies=[rate_limit("verification")],
)
def verify(
    record_version_id: UUID,
    body: VerificationRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=128,
            pattern=IDEMPOTENCY_KEY_PATTERN,
            description="Optional. Same key and body replays the original attempt.",
        ),
    ] = None,
) -> VerificationResponse:
    """Request a SIMULATED APAAR identity check (demo adapter only).

    A valid local APAAR format is never identity confirmation. Provider
    unavailability, timeout or a pending result is never a mismatch.
    """
    result, replayed = request_verification(
        session,
        user,
        record_version_id,
        body.purpose,
        body.consent_ref,
        cast(Settings, request.app.state.settings),
        retry_of=body.retry_of,
        idempotency_key=idempotency_key,
    )
    if replayed:
        response.status_code = 200
        response.headers["Idempotent-Replayed"] = "true"
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
    window = paginate_list(items, page, page_size)
    return Page[VerificationResponse](
        data=[verification_response(item) for item in window.data],
        pagination=window.pagination,
    )
