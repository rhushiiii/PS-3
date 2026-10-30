"""Route-level security sweep: no route can ship without a reviewed role decision.

ROLE_TABLE declares, for every non-public route, whether AICTE_MANAGER and
AUTHORIZED_VERIFIER may reach it. Add an entry here (and think about the roles)
whenever a route is added, or ``test_every_route_has_a_reviewed_entry`` fails.
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_credentials import activated_record
from test_validation import run_validation

from app.core.config import Settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.cases.models import ReviewCase
from app.modules.submissions.models import StudentRecordVersion

Headers = Callable[[str], dict[str, str]]
Route = tuple[str, str]
ALLOW, DENY = "ALLOW", "DENY"
YEAR = "2026-27"

PUBLIC: set[Route] = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/ready"),
    ("GET", "/openapi.json"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
    ("POST", "/api/v1/auth/demo-login"),
}

# (manager, verifier) access to each non-public route.
# Basis: require_metadata_role (institutions: admin/officer/manager), intake_actor
# (officer + own-institution admin), require_submission_role (admin/officer),
# analytics_user and the integrity overview (officer/manager), audit (officer),
# notifications (admin/officer), credential ISSUER/VERIFIER roles, report KIND_ROLES.
ROLE_TABLE: dict[Route, tuple[str, str]] = {
    ("GET", "/api/v1/me"): (ALLOW, ALLOW),
    ("GET", "/api/v1/institutions"): (ALLOW, DENY),
    ("GET", "/api/v1/institutions/{institution_id}"): (ALLOW, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/programmes"): (ALLOW, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/summary"): (ALLOW, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/intake"): (ALLOW, DENY),
    ("PATCH", "/api/v1/institutions/{institution_id}/intake/{rule_id}"): (DENY, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/intake/changes"): (DENY, DENY),
    ("POST", "/api/v1/institutions/{institution_id}/intake/simulate"): (DENY, DENY),
    ("POST", "/api/v1/institutions/{institution_id}/declarations"): (DENY, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/declarations"): (DENY, DENY),
    ("GET", "/api/v1/institutions/{institution_id}/declarations/latest"): (DENY, DENY),
    ("GET", "/api/v1/submissions/upload-policy"): (DENY, DENY),
    ("POST", "/api/v1/submissions"): (DENY, DENY),
    ("GET", "/api/v1/submissions"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/rows"): (DENY, DENY),
    ("POST", "/api/v1/submissions/{batch_id}/validate"): (DENY, DENY),
    ("POST", "/api/v1/submissions/{batch_id}/revalidate"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/validation-runs"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/validation-runs/{run_id}"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/findings"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/feedback.csv"): (DENY, DENY),
    ("POST", "/api/v1/submissions/{batch_id}/reviews"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/reviews/{review_id}"): (DENY, DENY),
    ("POST", "/api/v1/submissions/{batch_id}/activate"): (DENY, DENY),
    ("POST", "/api/v1/submissions/{batch_id}/intake-assessments"): (DENY, DENY),
    ("GET", "/api/v1/submissions/{batch_id}/intake-assessments"): (DENY, DENY),
    (
        "GET",
        "/api/v1/submissions/{batch_id}/intake-assessments/{assessment_id}",
    ): (DENY, DENY),
    ("GET", "/api/v1/records"): (DENY, DENY),
    ("GET", "/api/v1/records/{record_version_id}"): (DENY, DENY),
    ("POST", "/api/v1/records/{record_version_id}/apaar-verify"): (DENY, DENY),
    ("GET", "/api/v1/records/{record_version_id}/apaar-verify"): (DENY, DENY),
    ("POST", "/api/v1/cases"): (DENY, DENY),
    ("GET", "/api/v1/cases"): (DENY, DENY),
    ("GET", "/api/v1/cases/assignees"): (DENY, DENY),
    ("GET", "/api/v1/cases/{case_id}"): (DENY, DENY),
    ("POST", "/api/v1/cases/{case_id}/actions"): (DENY, DENY),
    ("GET", "/api/v1/notifications"): (DENY, DENY),
    ("GET", "/api/v1/notifications/unread-count"): (DENY, DENY),
    ("POST", "/api/v1/notifications/read-all"): (DENY, DENY),
    ("POST", "/api/v1/notifications/{notification_id}/read"): (DENY, DENY),
    ("GET", "/api/v1/integrity/overview"): (ALLOW, DENY),
    ("GET", "/api/v1/integrity/institutions/{institution_id}/signals"): (DENY, DENY),
    ("POST", "/api/v1/integrity/institutions/{institution_id}/decisions"): (
        DENY,
        DENY,
    ),
    ("GET", "/api/v1/integrity/institutions/{institution_id}/decisions"): (DENY, DENY),
    ("POST", "/api/v1/credentials"): (DENY, DENY),
    ("GET", "/api/v1/credentials"): (DENY, DENY),
    ("POST", "/api/v1/credentials/{credential_id}/revoke"): (DENY, DENY),
    ("POST", "/api/v1/credentials/verify"): (DENY, ALLOW),
    ("GET", "/api/v1/credentials/verifications"): (DENY, ALLOW),
    ("GET", "/api/v1/analytics/enrolment-trends"): (ALLOW, DENY),
    ("GET", "/api/v1/analytics/submission-completeness"): (ALLOW, DENY),
    ("GET", "/api/v1/analytics/intake-utilisation"): (ALLOW, DENY),
    ("GET", "/api/v1/analytics/case-performance"): (ALLOW, DENY),
    # Managers may export aggregate kinds; the probe uses open-cases (manager 403).
    ("GET", "/api/v1/reports/{kind}"): (DENY, DENY),
    ("GET", "/api/v1/audit/events"): (DENY, DENY),
    ("GET", "/api/v1/audit/actions"): (DENY, DENY),
    ("GET", "/api/v1/audit/events/{event_id}"): (DENY, DENY),
}
# Bodies that satisfy request validation, so the role check (not a 422) answers.
PLACEHOLDER = "00000000-0000-4000-8000-000000000001"
BODIES: dict[Route, dict[str, Any]] = {
    ("PATCH", "/api/v1/institutions/{institution_id}/intake/{rule_id}"): {
        "approved_seats": 10,
        "reason": "Synthetic reason",
    },
    ("POST", "/api/v1/institutions/{institution_id}/declarations"): {
        "programme_id": PLACEHOLDER,
        "academic_year": YEAR,
        "declared_total": 1,
        "basis": "Synthetic basis",
    },
    ("POST", "/api/v1/institutions/{institution_id}/intake/simulate"): {
        "programme_id": PLACEHOLDER,
        "academic_year": YEAR,
        "additions": [{"category": "REGULAR", "count": 1}],
    },
    ("POST", "/api/v1/cases"): {
        "category": "OTHER",
        "summary": "Synthetic summary",
        "record_version_ids": [PLACEHOLDER],
    },
    ("POST", "/api/v1/cases/{case_id}/actions"): {"action": "COMMENT"},
    ("POST", "/api/v1/credentials"): {"record_version_id": PLACEHOLDER},
    ("POST", "/api/v1/credentials/verify"): {
        "token": "synthetic",
        "purpose": "ADMISSION_CHECK",
        "consent_ref": "consent-demo-1",
    },
    ("POST", "/api/v1/credentials/{credential_id}/revoke"): {"reason": "Synthetic"},
    ("POST", "/api/v1/integrity/institutions/{institution_id}/decisions"): {
        "signal_key": "synthetic",
        "decision": "FALSE_POSITIVE",
        "reason": "Synthetic reason",
    },
    ("POST", "/api/v1/records/{record_version_id}/apaar-verify"): {
        "purpose": "AICTE_CASE_REVIEW",
        "consent_ref": "consent-demo-1",
    },
    ("POST", "/api/v1/submissions/{batch_id}/reviews"): {
        "validation_run_id": PLACEHOLDER
    },
    ("POST", "/api/v1/submissions/{batch_id}/activate"): {
        "review_id": PLACEHOLDER,
        "expected_scope_revision": 0,
        "confirm_complete_replacement": True,
        "acknowledge_review_warnings": True,
    },
}


def all_routes(app: FastAPI) -> set[Route]:
    """Flatten app.routes, including lazily included routers."""
    found: set[Route] = set()
    for route in app.routes:
        contexts = (
            list(route.effective_route_contexts())
            if hasattr(route, "effective_route_contexts")
            else [route]
        )
        for context in contexts:
            for method in (getattr(context, "methods", None) or set()) - {
                "HEAD",
                "OPTIONS",
            }:
                found.add((method, str(getattr(context, "path"))))  # noqa: B009
    return found


def url_for(path: str) -> str:
    return (
        path.replace("{kind}", "open-cases")
        .replace("{institution_id}", PLACEHOLDER)
        .replace("{rule_id}", PLACEHOLDER)
        .replace("{batch_id}", PLACEHOLDER)
        .replace("{run_id}", PLACEHOLDER)
        .replace("{review_id}", PLACEHOLDER)
        .replace("{assessment_id}", PLACEHOLDER)
        .replace("{record_version_id}", PLACEHOLDER)
        .replace("{case_id}", PLACEHOLDER)
        .replace("{notification_id}", PLACEHOLDER)
        .replace("{credential_id}", PLACEHOLDER)
        .replace("{event_id}", PLACEHOLDER)
    )


@pytest.fixture
def anonymous_client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings), base_url="http://localhost")


def test_every_route_has_a_reviewed_entry(settings: Settings) -> None:
    routes = all_routes(create_app(settings.model_copy(update={"demo_auth": False})))
    demo = all_routes(create_app(_demo_settings()))
    # demo-login only exists in DEMO_AUTH mode; it is explicitly public.
    assert routes | demo == set(ROLE_TABLE) | PUBLIC, (
        "New or removed routes need a reviewed ROLE_TABLE/PUBLIC entry: "
        f"{sorted((routes | demo) ^ (set(ROLE_TABLE) | PUBLIC))}"
    )
    assert not set(ROLE_TABLE) & PUBLIC


def _demo_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url=SecretStr("postgresql+psycopg://demo:synthetic@127.0.0.1:1/test"),
        app_env="local",
        demo_auth=True,
        demo_auth_secret=SecretStr("synthetic-test-key-" + "x" * 32),
    )


@pytest.mark.parametrize(("method", "path"), sorted(ROLE_TABLE))
def test_non_public_routes_require_authentication(
    anonymous_client: TestClient, method: str, path: str
) -> None:
    with anonymous_client as client:
        response = client.request(method, url_for(path), json={})
    assert response.status_code == 401, (method, path)
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(("method", "path"), sorted(ROLE_TABLE))
def test_manager_and_verifier_access_matches_the_table(
    client: TestClient, auth_headers: Headers, method: str, path: str
) -> None:
    for alias, expected in (
        ("demo_manager", ROLE_TABLE[(method, path)][0]),
        ("demo_verifier", ROLE_TABLE[(method, path)][1]),
    ):
        response = client.request(
            method,
            url_for(path),
            headers=auth_headers(alias),
            params={"academic_year": YEAR, "programme_id": PLACEHOLDER},
            json=BODIES.get((method, path), {}),
        )
        if expected == DENY:
            assert response.status_code == 403, (alias, method, path, response.text)
            assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
        else:
            assert response.status_code not in {401, 403}, (alias, method, path)


def test_manager_report_kinds_match_the_declared_rules(
    client: TestClient, auth_headers: Headers
) -> None:
    manager = auth_headers("demo_manager")
    for kind in (
        "enrolment-summary",
        "intake-utilisation",
        "submission-completeness",
        "resolution-times",
        "validation-findings",
    ):
        assert client.get(f"/api/v1/reports/{kind}", headers=manager).status_code == 200
    for kind in ("open-cases", "verification-activity"):
        assert client.get(f"/api/v1/reports/{kind}", headers=manager).status_code == 403


# ---------------------------------------------------- cross-institution isolation


def maple_resources(
    client: TestClient, auth_headers: Headers, session: Session
) -> dict[str, str]:
    """One resource of each kind that belongs to the Maple institution."""
    record_id = activated_record(client, auth_headers, session, institution="maple")
    record = session.get(StudentRecordVersion, UUID(record_id))
    assert record is not None
    officer = auth_headers("demo_officer")
    batch = str(record.batch_id)
    case = client.post(
        "/api/v1/cases",
        headers=officer,
        json={
            "category": "OTHER",
            "summary": "Synthetic isolation case",
            "record_version_ids": [record_id],
        },
    )
    assert case.status_code == 201, case.text
    assessment = client.post(
        f"/api/v1/submissions/{batch}/intake-assessments", headers=officer
    )
    assert assessment.status_code == 201, assessment.text
    run = run_validation(client, batch, officer, repeat=True)
    return {
        "institution_id": str(record.institution_id),
        "batch_id": batch,
        "record_version_id": record_id,
        "case_id": case.json()["id"],
        "assessment_id": assessment.json()["id"],
        "run_id": run["id"],
    }


ISOLATED_GET_ROUTES = [
    "/api/v1/institutions/{institution_id}",
    "/api/v1/institutions/{institution_id}/programmes",
    "/api/v1/institutions/{institution_id}/summary",
    "/api/v1/institutions/{institution_id}/intake",
    "/api/v1/institutions/{institution_id}/intake/changes",
    "/api/v1/institutions/{institution_id}/declarations",
    "/api/v1/integrity/institutions/{institution_id}/signals",
    "/api/v1/submissions/{batch_id}",
    "/api/v1/submissions/{batch_id}/rows",
    "/api/v1/submissions/{batch_id}/validation-runs",
    "/api/v1/submissions/{batch_id}/validation-runs/{run_id}",
    "/api/v1/submissions/{batch_id}/findings",
    "/api/v1/submissions/{batch_id}/feedback.csv",
    "/api/v1/submissions/{batch_id}/intake-assessments",
    "/api/v1/submissions/{batch_id}/intake-assessments/{assessment_id}",
    "/api/v1/records/{record_version_id}",
    "/api/v1/records/{record_version_id}/apaar-verify",
    "/api/v1/cases/{case_id}",
]


def test_isolated_routes_are_declared_routes() -> None:
    declared = {path for method, path in ROLE_TABLE if method == "GET"}
    assert set(ISOLATED_GET_ROUTES) <= declared


@pytest.mark.parametrize("template", ISOLATED_GET_ROUTES)
def test_institution_admin_cannot_read_another_institutions_resources(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
    template: str,
) -> None:
    resources = maple_resources(client, auth_headers, seeded_session)
    path = template.format(**resources)
    own_admin = auth_headers("cedar_admin")
    # Control: the owning institution's admin does reach the same resource.
    params = {"academic_year": YEAR}
    owner = client.get(path, headers=auth_headers("maple_admin"), params=params)
    assert owner.status_code == 200, (template, owner.text)
    other = client.get(path, headers=own_admin, params=params)
    assert other.status_code == 404, (template, other.status_code, other.text)
    assert other.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_unknown_ids_are_indistinguishable_from_other_institutions(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    resources = maple_resources(client, auth_headers, seeded_session)
    admin = auth_headers("cedar_admin")
    for template in ("/api/v1/cases/{case_id}", "/api/v1/submissions/{batch_id}"):
        foreign = client.get(template.format(**resources), headers=admin)
        missing = client.get(
            template.format(case_id=uuid4(), batch_id=uuid4()), headers=admin
        )
        assert foreign.status_code == missing.status_code == 404
        assert foreign.json()["error"]["message"] == missing.json()["error"]["message"]


def test_isolation_fixtures_belong_to_another_institution(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    resources = maple_resources(client, auth_headers, seeded_session)
    cedar = seeded_session.scalar(
        select(User.institution_id).where(User.demo_alias == "cedar_admin")
    )
    case = seeded_session.get(ReviewCase, UUID(resources["case_id"]))
    assert case is not None
    assert str(case.institution_id) == resources["institution_id"] != str(cedar)
