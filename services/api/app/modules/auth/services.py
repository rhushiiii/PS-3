from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from typing import Protocol
from uuid import UUID, uuid4

import jwt
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.modules.audit.services import record_action
from app.modules.auth.models import User

DEMO_ALIASES = frozenset(
    {
        "cedar_admin",
        "maple_admin",
        "willow_admin",
        "demo_officer",
        "demo_manager",
        "demo_officer_2",
        "demo_verifier",
    }
)
ISSUER = "sih26263-local-demo"
AUDIENCE = "sih26263-api"


def unauthenticated(code: str = "NOT_AUTHENTICATED") -> APIError:
    message = (
        "Demo session expired" if code == "SESSION_EXPIRED" else "Not authenticated"
    )
    return APIError(401, code, message, {"WWW-Authenticate": "Bearer"})


def require_demo_access(request: Request, settings: Settings) -> None:
    if not settings.demo_auth:
        raise unauthenticated()
    origin = request.headers.get("origin")
    if settings.demo_public_access:
        if origin is not None and origin not in settings.cors_origins:
            raise APIError(403, "DEMO_ORIGIN_DENIED", "Demo origin is not allowed")
        return
    if settings.app_env != "local":
        raise unauthenticated()
    peer = request.client.host if request.client else ""
    try:
        local_peer = ip_address(peer).is_loopback
    except ValueError:
        local_peer = False
    proxy_headers = any(
        key in {"forwarded", "via", "x-real-ip"} or key.startswith("x-forwarded-")
        for key in request.headers
    )
    if (
        not local_peer
        or request.url.hostname not in {"localhost", "127.0.0.1", "::1"}
        or proxy_headers
        or (origin is not None and origin not in settings.cors_origins)
    ):
        raise APIError(
            403, "DEMO_LOCAL_ONLY", "Demo access requires a direct local request"
        )


class TokenVerifier(Protocol):
    def authenticate(self, token: str, request: Request, session: Session) -> User: ...


class DemoTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        if not settings.demo_auth or (
            settings.app_env != "local" and not settings.demo_public_access
        ):
            raise ValueError("Demo authentication is disabled")
        assert settings.demo_auth_secret is not None
        self._key = settings.demo_auth_secret.get_secret_value()
        self._settings = settings
        self.ttl_seconds = settings.demo_token_ttl_seconds

    def issue(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user_id),
                "iss": ISSUER,
                "aud": AUDIENCE,
                "iat": now,
                "exp": now + timedelta(seconds=self.ttl_seconds),
                "jti": str(uuid4()),
                "auth_mode": "DEMO",
            },
            self._key,
            algorithm="HS256",
        )

    def verify(self, token: str) -> UUID:
        try:
            claims = jwt.decode(
                token,
                self._key,
                algorithms=["HS256"],
                issuer=ISSUER,
                audience=AUDIENCE,
                options={"require": ["sub", "exp", "iat", "iss", "aud", "jti"]},
            )
            if claims.get("auth_mode") != "DEMO":
                raise unauthenticated()
            return UUID(claims["sub"])
        except jwt.ExpiredSignatureError:
            raise unauthenticated("SESSION_EXPIRED") from None
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise unauthenticated() from None

    def authenticate(self, token: str, request: Request, session: Session) -> User:
        require_demo_access(request, self._settings)
        user = session.get(User, self.verify(token))
        if (
            user is None
            or not user.active
            or not user.is_demo
            or user.demo_alias not in DEMO_ALIASES
        ):
            raise unauthenticated()
        return user


def resolve_demo_user(session: Session, alias: str) -> User:
    if alias not in DEMO_ALIASES:
        raise unauthenticated()
    user = session.scalar(select(User).where(User.demo_alias == alias))
    if user is None or not user.active or not user.is_demo:
        raise unauthenticated()
    return user


def issue_demo_session(
    session: Session, user: User, verifier: DemoTokenVerifier
) -> str:
    token = verifier.issue(user.id)
    record_action(
        session,
        actor_id=user.id,
        institution_id=user.institution_id,
        action="DEMO_LOGIN",
        entity_type="users",
        entity_id=user.id,
    )
    # Return credentials only once their issuance audit has committed.
    session.commit()
    return token
