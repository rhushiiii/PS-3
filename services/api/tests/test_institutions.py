from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth.models import Role, User
from app.seed import seed_id

CEDAR = str(seed_id("institutions", "cedar"))
MAPLE = str(seed_id("institutions", "maple"))
OWN_PATHS = [
    "/api/v1/institutions",
    f"/api/v1/institutions/{CEDAR}",
    f"/api/v1/institutions/{CEDAR}/programmes",
    f"/api/v1/institutions/{CEDAR}/intake?academic_year=2026-27",
]


@pytest.mark.parametrize("path", OWN_PATHS)
def test_business_endpoints_require_auth(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("alias", ["demo_officer", "demo_manager"])
def test_directory_and_filters(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]], alias: str
) -> None:
    headers = auth_headers(alias)
    response = client.get("/api/v1/institutions?page_size=2", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2
    assert response.json()["pagination"] == {"page": 1, "page_size": 2, "total": 3}
    filtered = client.get("/api/v1/institutions?q=cedar", headers=headers).json()
    assert filtered["pagination"]["total"] == 1
    assert filtered["data"][0]["id"] == CEDAR
    assert client.get("/api/v1/institutions?q=%", headers=headers).json()["data"] == []
    assert (
        client.get("/api/v1/institutions?region=DEMO_REGION_2", headers=headers).json()[
            "data"
        ][0]["id"]
        == MAPLE
    )
    assert (
        client.get(f"/api/v1/institutions/{MAPLE}", headers=headers).status_code == 200
    )


def test_institution_admin_cannot_list_directory(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    assert (
        client.get(
            "/api/v1/institutions", headers=auth_headers("cedar_admin")
        ).status_code
        == 403
    )


def test_own_institution_programmes_and_intake(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("cedar_admin")
    assert (
        client.get(f"/api/v1/institutions/{CEDAR}", headers=headers).json()["name"]
        == "Demo Cedar Institute"
    )
    programmes = client.get(
        f"/api/v1/institutions/{CEDAR}/programmes", headers=headers
    ).json()
    assert programmes["pagination"]["total"] == 2
    assert all(row["institution_id"] == CEDAR for row in programmes["data"])
    programme = str(seed_id("programmes", "cedar/DEMO-COMP"))
    response = client.get(
        f"/api/v1/institutions/{CEDAR}/intake?academic_year=2026-27&programme_id={programme}",
        headers=headers,
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 5
    assert {row["category"]: row["approved_seats"] for row in rows} == {
        "REGULAR": 3,
        "SUPERNUMERARY": 1,
        "NRI": 1,
        "OCI": 1,
        "FOREIGN_NATIONAL": 1,
    }
    assert all(
        row["source_label"] == "DEMO" and row["rule_version"] == "DEMO-v1"
        for row in rows
    )
    assert "apaar" not in response.text.lower()


@pytest.mark.parametrize("suffix", ["", "/programmes", "/intake?academic_year=2026-27"])
def test_cross_institution_reads_denied(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]], suffix: str
) -> None:
    response = client.get(
        f"/api/v1/institutions/{MAPLE}{suffix}", headers=auth_headers("cedar_admin")
    )
    assert response.status_code == 404
    assert "Maple" not in response.text


def test_foreign_programme_filter_denied(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    programme = seed_id("programmes", "maple/DEMO-COMP")
    response = client.get(
        f"/api/v1/institutions/{CEDAR}/intake?academic_year=2026-27&programme_id={programme}",
        headers=auth_headers("cedar_admin"),
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "",
        "?academic_year=bad",
        "?academic_year=2026-29",
        "?academic_year=2026-27&page=0",
        "?academic_year=2026-27&page_size=101",
        "?academic_year=2026-27&programme_id=bad",
    ],
)
def test_intake_request_validation(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]], query: str
) -> None:
    response = client.get(
        f"/api/v1/institutions/{CEDAR}/intake{query}",
        headers=auth_headers("cedar_admin"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/institutions/not-a-uuid",
        "/api/v1/institutions?page=-1",
        "/api/v1/institutions?page_size=101",
    ],
)
def test_directory_invalid_parameters(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]], path: str
) -> None:
    assert client.get(path, headers=auth_headers("demo_officer")).status_code == 422


def test_missing_institution_and_empty_page(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    headers = auth_headers("demo_manager")
    assert (
        client.get(f"/api/v1/institutions/{uuid4()}", headers=headers).status_code
        == 404
    )
    result = client.get("/api/v1/institutions?page=10", headers=headers).json()
    assert result["data"] == [] and result["pagination"]["total"] == 3
    result = client.get(
        f"/api/v1/institutions/{CEDAR}/intake?academic_year=2025-26", headers=headers
    ).json()
    assert result["data"] == []


@pytest.mark.parametrize("path", OWN_PATHS)
def test_verifier_role_has_no_business_access(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    path: str,
) -> None:
    headers = auth_headers("cedar_admin")
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    user.role = Role.AUTHORIZED_VERIFIER
    seeded_session.commit()
    assert client.get(path, headers=headers).status_code == 403


def test_openapi_is_limited_to_implemented_milestones(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/auth/demo-login",
        "/api/v1/me",
        "/api/v1/institutions",
        "/api/v1/institutions/{institution_id}",
        "/api/v1/institutions/{institution_id}/programmes",
        "/api/v1/institutions/{institution_id}/intake",
        "/api/v1/institutions/{institution_id}/summary",
        "/api/v1/submissions",
        "/api/v1/submissions/upload-policy",
        "/api/v1/submissions/{batch_id}",
        "/api/v1/submissions/{batch_id}/rows",
        "/api/v1/submissions/{batch_id}/validate",
        "/api/v1/submissions/{batch_id}/revalidate",
        "/api/v1/submissions/{batch_id}/validation-runs",
        "/api/v1/submissions/{batch_id}/validation-runs/{run_id}",
        "/api/v1/submissions/{batch_id}/findings",
        "/api/v1/submissions/{batch_id}/feedback.csv",
        "/api/v1/submissions/{batch_id}/reviews",
        "/api/v1/submissions/{batch_id}/reviews/{review_id}",
        "/api/v1/submissions/{batch_id}/activate",
        "/api/v1/records/{record_version_id}/apaar-verify",
        "/api/v1/cases",
        "/api/v1/cases/{case_id}",
        "/api/v1/cases/{case_id}/actions",
    }
    assert "401" in paths["/api/v1/institutions"]["get"]["responses"]


def test_cors_allows_only_configured_local_origin(client: TestClient) -> None:
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/auth/demo-login", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    headers["Origin"] = "https://example.com"
    response = client.options("/api/v1/auth/demo-login", headers=headers)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
