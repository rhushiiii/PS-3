from typing import cast

from fastapi import APIRouter, Request, Response

from app.core.config import Settings
from app.core.http import ErrorResponse
from app.core.rate_limit import rate_limit_by_ip
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.auth.schemas import CurrentUserResponse, DemoLogin, TokenResponse
from app.modules.auth.services import (
    DemoTokenVerifier,
    issue_demo_session,
    require_demo_access,
    resolve_demo_user,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Identity"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
demo_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Local demo authentication"],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)


@router.get("/me", response_model=CurrentUserResponse)
def me(user: CurrentUser, response: Response) -> CurrentUserResponse:
    response.headers["Cache-Control"] = "no-store"
    return CurrentUserResponse.model_validate(user)


@demo_router.post(
    "/demo-login",
    response_model=TokenResponse,
    dependencies=[rate_limit_by_ip("demo_login")],
)
def demo_login(
    body: DemoLogin, request: Request, response: Response, session: DatabaseSession
) -> TokenResponse:
    settings = cast(Settings, request.app.state.settings)
    require_demo_access(request, settings)
    user = resolve_demo_user(session, body.demo_alias)
    verifier = DemoTokenVerifier(settings)
    token = issue_demo_session(session, user, verifier)
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(access_token=token, expires_in=verifier.ttl_seconds)
