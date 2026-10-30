"""Rate limiting, security headers, log redaction and the global body cap."""

import logging
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.core.config import Settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import (
    SECURITY_HEADERS,
    SecurityHeadersMiddleware,
    install_log_redaction,
    redact_text,
)
from app.main import create_app

Headers = Callable[[str], dict[str, str]]
JWS = "eyJhbGciOiJFZERTQSJ9.eyJzdWIiOiJzeW50aGV0aWMifQ.c2lnbmF0dXJlLXN5bnRoZXRpYw"
SYNTHETIC_ID = "900000000123"


def demo_settings(**overrides: object) -> Settings:
    return Settings(
        _env_file=None,
        database_url=SecretStr("postgresql+psycopg://demo:synthetic@127.0.0.1:1/test"),
        app_env="local",
        demo_auth=True,
        demo_auth_secret=SecretStr("synthetic-test-key-" + "x" * 32),
        **overrides,  # type: ignore[arg-type]
    )


@pytest.fixture
def small_body_client() -> Iterator[TestClient]:
    app = create_app(demo_settings(request_max_bytes=64))
    with TestClient(app, base_url="http://localhost") as client:
        yield client


# ------------------------------------------------------------------ rate limiter


def test_sliding_window_counts_and_expires() -> None:
    now = [0.0]
    limiter = SlidingWindowLimiter(window_seconds=60, clock=lambda: now[0])
    assert limiter.hit("b", "k", 2) is None
    now[0] = 10
    assert limiter.hit("b", "k", 2) is None
    now[0] = 20
    assert limiter.hit("b", "k", 2) == 40  # oldest hit leaves the window at t=60
    assert limiter.hit("b", "other", 2) is None  # keys are independent
    assert limiter.hit("other", "k", 2) is None  # buckets are independent
    now[0] = 60  # the first hit expired; rejected requests were never recorded
    assert limiter.hit("b", "k", 2) is None
    assert limiter.hit("b", "k", 2) == 10


def test_expired_keys_are_swept() -> None:
    now = [0.0]
    limiter = SlidingWindowLimiter(window_seconds=1, clock=lambda: now[0])
    for index in range(2000):
        limiter.hit("b", f"k{index}", 5)
    now[0] = 5
    for _ in range(1000):
        limiter.hit("b", "live", 5000)
    assert len(limiter._hits) < 100


def test_login_is_limited_per_ip_with_retry_after(
    application: FastAPI, client: TestClient
) -> None:
    application.state.settings = application.state.settings.model_copy(
        update={"rate_limit_demo_login_per_minute": 2}
    )
    body = {"demo_alias": "demo_officer"}
    for _ in range(2):
        assert client.post("/api/v1/auth/demo-login", json=body).status_code == 200
    limited = client.post("/api/v1/auth/demo-login", json=body)
    assert limited.status_code == 429
    assert 1 <= int(limited.headers["retry-after"]) <= 60
    error = limited.json()["error"]
    assert error["code"] == "RATE_LIMITED" and error["request_id"]
    assert limited.headers["cache-control"] == "no-store"


def test_authenticated_buckets_are_per_user_and_can_be_disabled(
    application: FastAPI, client: TestClient, auth_headers: Headers
) -> None:
    application.state.settings = application.state.settings.model_copy(
        update={"rate_limit_exports_per_minute": 2}
    )
    officer, manager = auth_headers("demo_officer"), auth_headers("demo_manager")
    url = "/api/v1/reports/enrolment-summary"
    assert [client.get(url, headers=officer).status_code for _ in range(2)] == [200] * 2
    assert client.get(url, headers=officer).status_code == 429
    assert client.get(url, headers=manager).status_code == 200  # own budget
    # Authentication comes first: no credentials is 401, never a consumed budget.
    assert client.get(url).status_code == 401
    application.state.settings = application.state.settings.model_copy(
        update={"rate_limit_enabled": False}
    )
    assert client.get(url, headers=officer).status_code == 200


@pytest.mark.parametrize(
    ("setting", "method", "path", "body"),
    [
        ("rate_limit_cases_per_minute", "POST", "/api/v1/cases", {}),
        ("rate_limit_credentials_per_minute", "POST", "/api/v1/credentials", {}),
        (
            "rate_limit_verification_per_minute",
            "POST",
            "/api/v1/records/00000000-0000-4000-8000-000000000001/apaar-verify",
            {},
        ),
        (
            "rate_limit_intake_per_minute",
            "POST",
            "/api/v1/institutions/00000000-0000-4000-8000-000000000001/intake/simulate",
            {},
        ),
        (
            "rate_limit_reviews_per_minute",
            "POST",
            "/api/v1/submissions/00000000-0000-4000-8000-000000000001/reviews",
            {},
        ),
        ("rate_limit_uploads_per_minute", "POST", "/api/v1/submissions", {}),
    ],
)
def test_each_protected_bucket_returns_429(
    application: FastAPI,
    client: TestClient,
    auth_headers: Headers,
    setting: str,
    method: str,
    path: str,
    body: dict[str, object],
) -> None:
    application.state.settings = application.state.settings.model_copy(
        update={setting: 1}
    )
    headers = auth_headers("demo_officer")
    first = client.request(method, path, headers=headers, json=body)
    assert first.status_code != 429
    second = client.request(method, path, headers=headers, json=body)
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMITED"


def test_retry_after_is_exposed_through_cors(
    application: FastAPI, client: TestClient
) -> None:
    application.state.settings = application.state.settings.model_copy(
        update={"rate_limit_demo_login_per_minute": 1}
    )
    origin = {"Origin": "http://localhost:3000"}
    body = {"demo_alias": "demo_officer"}
    client.post("/api/v1/auth/demo-login", json=body, headers=origin)
    limited = client.post("/api/v1/auth/demo-login", json=body, headers=origin)
    assert limited.status_code == 429
    exposed = limited.headers["access-control-expose-headers"]
    assert "Retry-After" in exposed and "Content-Disposition" in exposed


# ------------------------------------------------------------------ headers


def test_security_headers_on_success_error_and_unknown_routes() -> None:
    app = create_app(demo_settings())
    with TestClient(app, base_url="http://localhost") as client:
        for path, status in (
            ("/api/v1/health", 200),
            ("/api/v1/me", 401),
            ("/api/v1/nope", 404),
        ):
            response = client.get(path)
            assert response.status_code == status, path
            for name, value in SECURITY_HEADERS.items():
                assert response.headers[name] == value, (path, name)
            assert response.headers["cache-control"] == "no-store", path
        docs = client.get("/docs")
        assert docs.headers["x-content-type-options"] == "nosniff"
        assert "cache-control" not in docs.headers  # default applies to /api/ only


def test_existing_cache_control_is_not_overridden() -> None:
    async def page(_: object) -> PlainTextResponse:
        return PlainTextResponse("x", headers={"Cache-Control": "max-age=5"})

    app = Starlette(routes=[Route("/api/v1/cached", page)])
    app.add_middleware(SecurityHeadersMiddleware)
    response = TestClient(app).get("/api/v1/cached")
    assert response.headers["cache-control"] == "max-age=5"
    assert response.headers["x-frame-options"] == "DENY"
    assert len(response.headers.get_list("x-frame-options")) == 1


# ------------------------------------------------------------------ log redaction


def test_redact_text_masks_identifiers_and_credentials() -> None:
    text = (
        f"id {SYNTHETIC_ID} ok 12345 short; Authorization: Bearer abc.def-ghi; "
        f"token {JWS}; Idempotency-Key: key-12345678"
    )
    cleaned = redact_text(text)
    assert SYNTHETIC_ID not in cleaned and JWS not in cleaned
    assert "abc.def-ghi" not in cleaned and "key-12345678" not in cleaned
    assert "12345 short" in cleaned  # fewer than 12 digits stay readable
    assert "Bearer [MASKED]" in cleaned


def test_log_records_are_redacted_for_messages_args_and_tracebacks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    install_log_redaction()
    install_log_redaction()  # idempotent
    with caplog.at_level(logging.INFO):
        logging.getLogger("app.test").info("verify %s now", SYNTHETIC_ID)
        logging.getLogger("uvicorn.error").warning(
            "auth failed: Bearer %s / %s", "opaque-token-value", JWS
        )
        logging.getLogger("uvicorn.access").info(
            "headers %s", {"idempotency-key": "secret-key-value"}
        )
        try:
            raise ValueError(f"bad apaar {SYNTHETIC_ID}")
        except ValueError:
            logging.getLogger("app.test").exception("failure")
    output = caplog.text
    for secret in (SYNTHETIC_ID, "opaque-token-value", JWS, "secret-key-value"):
        assert secret not in output
    assert "[MASKED]" in output
    assert caplog.records[0].getMessage() == "verify [MASKED] now"


def test_create_app_installs_redaction(caplog: pytest.LogCaptureFixture) -> None:
    create_app(demo_settings())
    with caplog.at_level(logging.INFO):
        logging.getLogger("anything").error("value %d", int(SYNTHETIC_ID))
    assert SYNTHETIC_ID not in caplog.text


# ------------------------------------------------------------------ body cap


def test_declared_oversized_body_is_rejected(small_body_client: TestClient) -> None:
    response = small_body_client.post(
        "/api/v1/auth/demo-login", json={"demo_alias": "x" * 200}
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
    assert response.json()["error"]["request_id"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_chunked_body_is_capped_on_received_bytes(
    small_body_client: TestClient,
) -> None:
    def chunks() -> Iterator[bytes]:
        yield b'{"demo_alias": "'
        for _ in range(10):  # no Content-Length: only received bytes can be counted
            yield b"x" * 20
        yield b'"}'

    response = small_body_client.post(
        "/api/v1/auth/demo-login",
        content=chunks(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_upload_route_keeps_its_own_bounds(small_body_client: TestClient) -> None:
    # Exempt from the global cap: it reaches authentication (401), not a 413.
    response = small_body_client.post(
        "/api/v1/submissions", content=b"x" * 500, headers={"Content-Type": "text/csv"}
    )
    assert response.status_code == 401


def test_body_within_cap_is_not_rejected(small_body_client: TestClient) -> None:
    response = small_body_client.post(
        "/api/v1/auth/demo-login", json={"demo_alias": "short"}
    )
    assert response.status_code != 413
