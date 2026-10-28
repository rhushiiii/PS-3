from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_validation import csv_data, upload

from app.core.config import Settings
from app.modules.submissions.models import StudentRecordVersion
from app.modules.verification.models import ApaarVerification


def record_id(session: Session, batch_id: str) -> str:
    record = session.scalar(
        select(StudentRecordVersion).where(StudentRecordVersion.batch_id == batch_id)
    )
    assert record is not None
    return str(record.id)


def verify(
    client: TestClient,
    record: str,
    headers: dict[str, str],
    *,
    purpose: str = "AICTE_CASE_REVIEW",
    consent_ref: str = "consent-demo-1",
) -> Any:
    return client.post(
        f"/api/v1/records/{record}/apaar-verify",
        headers=headers,
        json={"purpose": purpose, "consent_ref": consent_ref},
    )


@pytest.mark.parametrize(
    ("apaar_id", "expected_status"),
    [
        ("900000000001", "SIMULATED_MATCH"),
        ("900000000002", "SIMULATED_MISMATCH"),
        ("900000000003", "SOURCE_UNAVAILABLE"),
        ("900000000009", "PENDING"),
    ],
)
def test_officer_verification_fixtures_are_deterministic(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    apaar_id: str,
    expected_status: str,
) -> None:
    admin = auth_headers("cedar_admin")
    identifier = upload(client, admin, csv_data(apaar_id=apaar_id))
    record = record_id(seeded_session, identifier)
    outcome = verify(client, record, auth_headers("demo_officer"))
    assert outcome.status_code == 201, outcome.text
    body = outcome.json()
    assert body["status"] == expected_status
    assert body["adapter_type"] == "MOCK_V1"
    assert body["evidence"]["source_label"] == "SIMULATED"


def test_institution_admin_cannot_request_verification(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    admin = auth_headers("cedar_admin")
    identifier = upload(client, admin)
    response = client.post(
        "/api/v1/records/00000000-0000-0000-0000-000000000000/apaar-verify",
        headers=admin,
        json={"purpose": "AICTE_CASE_REVIEW", "consent_ref": "consent-demo-1"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert identifier


def test_manager_cannot_request_or_read_verification(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    identifier = upload(client, admin)
    record = record_id(seeded_session, identifier)
    manager = auth_headers("demo_manager")
    outcome = verify(client, record, manager)
    assert outcome.status_code == 403
    response = client.get(f"/api/v1/records/{record}/apaar-verify", headers=manager)
    assert response.status_code == 403


def test_institution_admin_reads_own_history_but_not_other_institutions(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    cedar_admin = auth_headers("cedar_admin")
    identifier = upload(client, cedar_admin)
    record = record_id(seeded_session, identifier)
    verify(client, record, auth_headers("demo_officer"))

    own = client.get(f"/api/v1/records/{record}/apaar-verify", headers=cedar_admin)
    assert own.status_code == 200
    assert own.json()["pagination"]["total"] == 1

    maple_admin = auth_headers("maple_admin")
    other = client.get(f"/api/v1/records/{record}/apaar-verify", headers=maple_admin)
    assert other.status_code == 404


def test_missing_matching_key_never_fabricates_a_result(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    demo_settings: Settings,
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    identifier = upload(client, admin)
    record = record_id(seeded_session, identifier)
    demo_settings.apaar_matching_key = None
    outcome = verify(client, record, auth_headers("demo_officer"))
    assert outcome.status_code == 422
    assert outcome.json()["error"]["code"] == "MATCHING_CONFIGURATION_UNAVAILABLE"
    assert seeded_session.scalar(select(ApaarVerification).limit(1)) is None


def test_history_orders_newest_first_and_is_immutable(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    identifier = upload(client, admin)
    record = record_id(seeded_session, identifier)
    first = verify(client, record, officer).json()
    second = verify(client, record, officer).json()

    history = client.get(f"/api/v1/records/{record}/apaar-verify", headers=admin)
    assert history.status_code == 200
    items = history.json()["data"]
    assert [item["id"] for item in items] == [second["id"], first["id"]]

    row = seeded_session.scalar(
        select(ApaarVerification).where(ApaarVerification.id == first["id"])
    )
    assert row is not None
    row.status = "SIMULATED_MISMATCH"
    with pytest.raises(DBAPIError):
        seeded_session.commit()
    seeded_session.rollback()
