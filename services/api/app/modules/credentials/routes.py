from uuid import UUID

from fastapi import APIRouter, Request, Response

from app.core.http import ErrorResponse, Now, no_store, settings_of
from app.core.pagination import Page, PageNumber, PageSize
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.credentials.schemas import (
    CredentialSummary,
    IssueRequest,
    IssueResponse,
    RevocationResponse,
    RevokeRequest,
    VerificationLogEntry,
    VerifyRequest,
    VerifyResponse,
)
from app.modules.credentials.services import (
    issue_credential,
    list_credentials,
    revoke_credential,
    verification_log,
    verify_credential,
)

router = APIRouter(
    prefix="/api/v1/credentials",
    tags=["Admission credentials (DEMO)"],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 500, 503)
    },
)


@router.post(
    "",
    response_model=IssueResponse,
    status_code=201,
    dependencies=[rate_limit("credentials")],
)
def issue(
    body: IssueRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    now: Now,
) -> IssueResponse:
    """Issue a signed DEMO credential for an ACTIVE record in the current snapshot.

    The token is returned once and never stored. Claims exclude APAAR and names.
    """
    result = issue_credential(
        session, user, body.record_version_id, settings_of(request), now
    )
    no_store(response)
    return result


@router.get("", response_model=Page[CredentialSummary])
def list_issued(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[CredentialSummary]:
    """List issued credentials in scope. Tokens are never returned here."""
    no_store(response)
    return list_credentials(session, user, page, page_size)


@router.post("/{credential_id}/revoke", response_model=RevocationResponse)
def revoke(
    credential_id: UUID,
    body: RevokeRequest,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
) -> RevocationResponse:
    no_store(response)
    return revoke_credential(session, user, credential_id, body.reason)


@router.post(
    "/verify",
    response_model=VerifyResponse,
    dependencies=[rate_limit("credentials")],
)
def verify(
    body: VerifyRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    now: Now,
) -> VerifyResponse:
    """Verify a presented credential token (DEMO).

    A QR code or scan is only a carrier for the token string; the Ed25519
    signature check is what establishes authenticity, never a database value
    alone. Purpose and consent_ref are mandatory (default deny). The token is
    not stored or logged. INVALID results reveal no claims.
    """
    no_store(response)
    return verify_credential(
        session,
        user,
        body.token,
        body.purpose,
        body.consent_ref,
        settings_of(request),
        now,
    )


@router.get("/verifications", response_model=Page[VerificationLogEntry])
def verifications(
    response: Response,
    user: CurrentUser,
    session: DatabaseSession,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[VerificationLogEntry]:
    """Verification access log: verifiers see their own, officers see all."""
    no_store(response)
    return verification_log(session, user, page, page_size)
