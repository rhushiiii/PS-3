from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError as DriverOperationalError
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError, TimeoutError

from app.core.config import Settings
from app.core.database import get_engine
from app.main import create_app


def test_liveness_never_connects_to_database(settings: Settings) -> None:
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = AssertionError(
        "Liveness must not contact the database"
    )
    with patch("app.main.build_engine", return_value=engine):
        with TestClient(create_app(settings)) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            engine.connect.assert_not_called()
        engine.dispose.assert_called_once()


def test_readiness_executes_select_one(settings: Settings) -> None:
    engine = MagicMock(spec=Engine)
    application = create_app(settings)
    application.dependency_overrides[get_engine] = lambda: engine
    with TestClient(application) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "reachable"}
    statement = engine.connect.return_value.__enter__.return_value.execute.call_args[0][
        0
    ]
    assert str(statement) == "SELECT 1"


@pytest.mark.parametrize("stage", ["connect", "execute"])
@pytest.mark.parametrize("error_type", [OperationalError, TimeoutError])
def test_readiness_failure_preserves_liveness(
    settings: Settings, stage: str, error_type: type[Exception]
) -> None:
    engine = MagicMock(spec=Engine)
    error = (
        OperationalError("SELECT 1", {}, DriverOperationalError("synthetic-secret"))
        if error_type is OperationalError
        else TimeoutError("synthetic-secret")
    )
    if stage == "connect":
        engine.connect.side_effect = error
    else:
        engine.connect.return_value.__enter__.return_value.execute.side_effect = error
    application = create_app(settings)
    application.dependency_overrides[get_engine] = lambda: engine
    with TestClient(application) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "database": "unreachable"}
        assert "synthetic-secret" not in response.text
        assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_actual_unavailable_postgresql_does_not_prevent_startup(
    settings: Settings,
) -> None:
    # Loopback port 1 is deliberately unavailable; no SQLite or external service.
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/ready").status_code == 503
        assert client.get("/api/v1/health").status_code == 200


def test_openapi_documents_readiness_failure(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        schema = client.get("/openapi.json").json()
        assert "503" in schema["paths"]["/api/v1/ready"]["get"]["responses"]
        assert client.get("/docs").status_code == 200


def test_cors_rejects_unconfigured_origin(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/v1/health", headers={"Origin": "https://example.com"}
        )
        assert "access-control-allow-origin" not in response.headers


def test_cors_allows_idempotency_key_and_exposes_replay_header(
    settings: Settings,
) -> None:
    origin = settings.cors_origins[0]
    with patch("app.main.build_engine", return_value=MagicMock(spec=Engine)):
        with TestClient(create_app(settings)) as client:
            preflight = client.options(
                "/api/v1/submissions",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "idempotency-key",
                },
            )
            assert preflight.status_code == 200
            assert (
                "idempotency-key"
                in preflight.headers["access-control-allow-headers"].lower()
            )
            simple = client.get("/api/v1/health", headers={"Origin": origin})
            assert (
                "Idempotent-Replayed" in simple.headers["access-control-expose-headers"]
            )
