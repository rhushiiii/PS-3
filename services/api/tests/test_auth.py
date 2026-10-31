from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError as DriverOperationalError
from pydantic import SecretStr, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.config import Settings
from app.main import create_app
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.auth.services import (
    AUDIENCE,
    ISSUER,
    DemoTokenVerifier,
    require_demo_access,
)
from app.modules.institutions.models import Institution
from app.seed import seed_id


@pytest.mark.parametrize(
    "overrides",
    [
        {"app_env": "production", "demo_auth_secret": SecretStr("x" * 48)},
        {"app_env": "local", "demo_auth_secret": None},
        {"app_env": "local", "demo_auth_secret": SecretStr("short")},
        {
            "app_env": "local",
            "demo_auth_secret": SecretStr("x" * 48),
            "cors_origins": ["*"],
        },
        {
            "app_env": "local",
            "demo_auth_secret": SecretStr("x" * 48),
            "cors_origins": ["https://example.com"],
        },
    ],
)
def test_demo_configuration_fails_closed(
    settings: Settings, overrides: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "database_url": settings.database_url,
                "demo_auth": True,
                **overrides,
            }
        )


def test_public_demo_requires_explicit_https_origin_and_secret(
    settings: Settings,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url=settings.database_url,
            app_env="production",
            demo_auth=True,
            demo_public_access=True,
            demo_auth_secret=SecretStr("x" * 48),
            cors_origins=["http://example.com"],
        )
    public = Settings(
        _env_file=None,
        database_url=settings.database_url,
        app_env="production",
        demo_auth=True,
        demo_public_access=True,
        demo_auth_secret=SecretStr("x" * 48),
        cors_origins=["https://example.com"],
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/demo-login",
            "scheme": "https",
            "server": ("api.example.com", 443),
            "client": ("203.0.113.10", 1234),
            "headers": [(b"origin", b"https://example.com")],
        }
    )
    require_demo_access(request, public)
    assert DemoTokenVerifier(public).ttl_seconds == 900


def test_disabled_login_and_authentication(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        assert (
            client.post(
                "/api/v1/auth/demo-login", json={"demo_alias": "cedar_admin"}
            ).status_code
            == 404
        )
        assert (
            client.get(
                "/api/v1/me", headers={"Authorization": "Bearer invalid"}
            ).status_code
            == 401
        )
        assert (
            "/api/v1/auth/demo-login" not in client.get("/openapi.json").json()["paths"]
        )


def test_login_current_identity_and_audit(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    headers = auth_headers("cedar_admin")
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(seed_id("users", "cedar_admin")),
        "role": "INSTITUTION_ADMIN",
        "institution_id": str(seed_id("institutions", "cedar")),
        "demo_mode": True,
    }
    assert response.headers["cache-control"] == "no-store"
    event = seeded_session.scalar(
        select(AuditEvent).where(AuditEvent.action == "DEMO_LOGIN")
    )
    assert event is not None and event.actor_id == seed_id("users", "cedar_admin")
    assert event.occurred_at.tzinfo is not None
    assert "Bearer" not in str(event.metadata_redacted)
    assert "access_token" not in str(event.metadata_redacted)


@pytest.mark.parametrize(
    "body",
    [
        {"demo_alias": "unknown"},
        {"demo_alias": ""},
        {},
        {"demo_alias": "cedar_admin", "role": "AICTE_OFFICER"},
        {"demo_alias": "cedar_admin", "institution_id": str(uuid4())},
    ],
)
def test_login_rejects_invalid_payloads(
    client: TestClient, body: dict[str, str]
) -> None:
    response = client.post("/api/v1/auth/demo-login", json=body)
    assert response.status_code in {401, 422}
    assert "access_token" not in response.json()


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "example.com"},
        {"Origin": "https://example.com"},
        {"Origin": "null"},
        {"Forwarded": "for=127.0.0.1"},
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Forwarded-Host": "localhost"},
        {"Via": "proxy"},
        {"X-Real-IP": "127.0.0.1"},
    ],
)
def test_demo_login_rejects_proxy_host_and_origin(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/auth/demo-login", json={"demo_alias": "cedar_admin"}, headers=headers
    )
    assert response.status_code == 403


def test_nonlocal_peer_cannot_login(application: FastAPI) -> None:
    with TestClient(
        application, base_url="http://localhost", client=("203.0.113.10", 1234)
    ) as client:
        response = client.post(
            "/api/v1/auth/demo-login", json={"demo_alias": "cedar_admin"}
        )
        assert response.status_code == 403


def token_with_claims(settings: Settings, overrides: dict[str, object]) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": str(seed_id("users", "cedar_admin")),
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "jti": str(uuid4()),
        "auth_mode": "DEMO",
    }
    claims.update(overrides)
    assert settings.demo_auth_secret is not None
    return jwt.encode(
        claims, settings.demo_auth_secret.get_secret_value(), algorithm="HS256"
    )


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "wrong"},
        {"aud": "wrong"},
        {"sub": "not-a-uuid"},
        {"sub": str(uuid4())},
        {"auth_mode": "OFFICIAL"},
        {"exp": "not-a-date"},
        {"iat": datetime.now(UTC) + timedelta(days=1)},
    ],
)
def test_invalid_token_claims(
    client: TestClient, demo_settings: Settings, claims: dict[str, object]
) -> None:
    token = token_with_claims(demo_settings, claims)
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert token not in response.text


def test_expiry_is_explicit(client: TestClient, demo_settings: Settings) -> None:
    token = token_with_claims(
        demo_settings, {"exp": datetime.now(UTC) - timedelta(seconds=1)}
    )
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


@pytest.mark.parametrize(
    "authorization", [None, "Basic value", "Bearer invalid", "Bearer"]
)
def test_missing_or_malformed_token(
    client: TestClient, authorization: str | None
) -> None:
    headers = {} if authorization is None else {"Authorization": authorization}
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_token_claims_cannot_grant_roles(
    client: TestClient, demo_settings: Settings
) -> None:
    token = token_with_claims(
        demo_settings,
        {
            "role": "AICTE_OFFICER",
            "institution_id": str(seed_id("institutions", "maple")),
        },
    )
    headers = {"Authorization": "Bearer " + token}
    assert (
        client.get("/api/v1/me", headers=headers).json()["role"] == "INSTITUTION_ADMIN"
    )
    assert client.get("/api/v1/institutions", headers=headers).status_code == 403


@pytest.mark.parametrize("state", ["inactive", "not_demo", "institution_inactive"])
def test_identity_changes_take_effect_immediately(
    client: TestClient,
    seeded_session: Session,
    auth_headers: Callable[[str], dict[str, str]],
    state: str,
) -> None:
    headers = auth_headers("cedar_admin")
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    if state == "inactive":
        user.active = False
    elif state == "not_demo":
        user.is_demo = False
    else:
        institution = seeded_session.get(Institution, user.institution_id)
        assert institution is not None
        institution.active = False
    seeded_session.commit()
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_audit_failure_returns_no_token(client: TestClient) -> None:
    with patch(
        "app.modules.auth.services.record_action",
        side_effect=OperationalError("", {}, DriverOperationalError("sensitive")),
    ):
        response = client.post(
            "/api/v1/auth/demo-login", json={"demo_alias": "cedar_admin"}
        )
    assert response.status_code == 503
    assert "sensitive" not in response.text and "access_token" not in response.text


def test_no_verifier_in_production(settings: Settings) -> None:
    with pytest.raises(ValueError):
        DemoTokenVerifier(settings)


@pytest.mark.parametrize("tampering", ["signature", "algorithm", "missing_expiry"])
def test_token_signature_algorithm_and_required_expiry(
    client: TestClient, demo_settings: Settings, tampering: str
) -> None:
    token = token_with_claims(demo_settings, {})
    # Decode only to construct deliberately invalid test inputs, never in the app.
    claims = jwt.decode(token, options={"verify_signature": False})
    assert demo_settings.demo_auth_secret is not None
    key = demo_settings.demo_auth_secret.get_secret_value()
    algorithm = "HS256"
    if tampering == "signature":
        key = "different-synthetic-key-" + "z" * 32
    elif tampering == "algorithm":
        algorithm = "HS384"
    else:
        del claims["exp"]
    token = jwt.encode(claims, key, algorithm=algorithm)
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401


def test_demo_bearer_cannot_be_used_from_nonlocal_peer(
    application: FastAPI, demo_settings: Settings
) -> None:
    token = token_with_claims(demo_settings, {})
    with TestClient(
        application, base_url="http://localhost", client=("203.0.113.10", 1234)
    ) as client:
        assert (
            client.get(
                "/api/v1/me", headers={"Authorization": "Bearer " + token}
            ).status_code
            == 403
        )


def test_token_from_local_mode_is_rejected_when_demo_disabled(
    settings: Settings,
) -> None:
    enabled = Settings(
        _env_file=None,
        database_url=settings.database_url,
        app_env="local",
        demo_auth=True,
        demo_auth_secret=SecretStr("synthetic-test-key-" + "x" * 32),
    )
    token = token_with_claims(enabled, {})
    with TestClient(create_app(settings)) as client:
        assert (
            client.get(
                "/api/v1/me", headers={"Authorization": "Bearer " + token}
            ).status_code
            == 401
        )


def test_auth_database_outage_keeps_liveness(settings: Settings) -> None:
    enabled = Settings(
        _env_file=None,
        database_url=settings.database_url,
        app_env="local",
        demo_auth=True,
        demo_auth_secret=SecretStr("synthetic-test-key-" + "x" * 32),
    )
    token = token_with_claims(enabled, {})
    with TestClient(
        create_app(enabled), base_url="http://localhost", client=("127.0.0.1", 1234)
    ) as client:
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token}
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "synthetic-secret" not in response.text
        assert client.get("/api/v1/health").status_code == 200
