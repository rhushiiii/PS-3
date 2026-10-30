import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_validation import csv_data, upload

from app.core.config import Settings
from app.modules.audit.models import AuditEvent
from app.modules.submissions.models import StudentRecordVersion
from app.modules.verification import services
from app.modules.verification.models import ApaarVerification
from app.modules.verification.provider import VerificationResult


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
    retry_of: str | None = None,
) -> Any:
    body: dict[str, Any] = {"purpose": purpose, "consent_ref": consent_ref}
    if retry_of is not None:
        body["retry_of"] = retry_of
    return client.post(
        f"/api/v1/records/{record}/apaar-verify", headers=headers, json=body
    )


def row_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(ApaarVerification)) or 0


def one_record(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    session: Session,
    apaar_id: str = "900000000009",
) -> str:
    identifier = upload(
        client, auth_headers("cedar_admin"), csv_data(apaar_id=apaar_id)
    )
    return record_id(session, identifier)


@pytest.mark.parametrize(
    ("apaar_id", "expected_status"),
    [
        ("900000000001", "SIMULATED_MATCH"),
        ("900000000002", "SIMULATED_MISMATCH"),
        ("900000000003", "SOURCE_UNAVAILABLE"),
        ("900000000004", "SOURCE_TIMEOUT"),
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


def test_format_and_identity_results_are_separate(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    body = verify(client, record, auth_headers("demo_officer")).json()
    assert body["format_validation"] == {
        "valid": True,
        "rule": "ASCII_DIGITS_LENGTH_12",
        "note": "format check is local; not identity verification",
    }
    identity = body["identity_verification"]
    # A syntactically valid identifier is not confirmed by that fact alone.
    assert identity["status"] == "PENDING"
    assert identity["source_type"] == "SIMULATED"
    assert identity["provenance_label"].startswith("SIMULATED")
    assert identity["provider_request_id"] == body["provider_request_id"]
    assert identity["provider_request_id"].startswith("req_")
    assert identity["requested_at"] and identity["completed_at"]


def test_provider_request_ids_are_unique_per_attempt(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    officer = auth_headers("demo_officer")
    ids = {verify(client, record, officer).json()["provider_request_id"] for _ in "ab"}
    assert len(ids) == 2


class ExplodingProvider:
    ADAPTER_TYPE = "MOCK_V1"

    def verify(
        self, apaar_match_hash_hex: str, *, purpose: str, consent_ref: str
    ) -> VerificationResult:
        raise RuntimeError("boom 900000000009")


class SlowProvider:
    ADAPTER_TYPE = "MOCK_V1"

    def verify(
        self, apaar_match_hash_hex: str, *, purpose: str, consent_ref: str
    ) -> VerificationResult:
        time.sleep(0.5)
        raise AssertionError("result must be discarded")


def test_provider_exception_is_unavailable_never_mismatch(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    monkeypatch.setattr(services, "build_provider", lambda key: ExplodingProvider())
    outcome = verify(client, record, auth_headers("demo_officer"))
    assert outcome.status_code == 201, outcome.text
    body = outcome.json()
    assert body["status"] == "SOURCE_UNAVAILABLE"
    assert body["evidence"]["failure"] == "PROVIDER_ERROR"
    assert "900000000009" not in outcome.text and "boom" not in outcome.text
    assert "MISMATCH" not in outcome.text


def test_provider_timeout_is_recorded_as_source_timeout(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    demo_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    monkeypatch.setattr(services, "build_provider", lambda key: SlowProvider())
    demo_settings.apaar_provider_timeout_seconds = 0.05
    outcome = verify(client, record, auth_headers("demo_officer"))
    assert outcome.status_code == 201, outcome.text
    assert outcome.json()["status"] == "SOURCE_TIMEOUT"
    assert outcome.json()["evidence"]["failure"] == "PROVIDER_TIMEOUT"


def test_idempotent_replay_returns_original_without_new_row_or_audit(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    officer = {**auth_headers("demo_officer"), "Idempotency-Key": "key-abcdef-1"}
    first = verify(client, record, officer)
    audits = seeded_session.scalar(
        select(func.count())
        .select_from(AuditEvent)
        .where(AuditEvent.action == "APAAR_VERIFICATION_REQUESTED")
    )
    second = verify(client, record, officer)
    assert first.status_code == 201
    assert "idempotent-replayed" not in first.headers
    assert second.status_code == 200
    assert second.headers["Idempotent-Replayed"] == "true"
    assert second.json() == first.json()
    rows = seeded_session.scalar(select(func.count()).select_from(ApaarVerification))
    assert rows == 1
    assert (
        seeded_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "APAAR_VERIFICATION_REQUESTED")
        )
        == audits
    )


def test_idempotency_key_reuse_with_different_request_conflicts(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    officer = {**auth_headers("demo_officer"), "Idempotency-Key": "key-abcdef-2"}
    assert verify(client, record, officer).status_code == 201
    other = verify(client, record, officer, purpose="DIFFERENT_PURPOSE")
    assert other.status_code == 409
    assert other.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert (
        seeded_session.scalar(select(func.count()).select_from(ApaarVerification)) == 1
    )


@pytest.mark.parametrize(
    "key", ["short", "bad key with spaces", "x" * 129, "a/b/c/d/e/f"]
)
def test_malformed_idempotency_key_is_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    key: str,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    headers = {**auth_headers("demo_officer"), "Idempotency-Key": key}
    assert verify(client, record, headers).status_code == 422
    assert (
        seeded_session.scalar(select(func.count()).select_from(ApaarVerification)) == 0
    )


def test_retry_rules(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    officer = auth_headers("demo_officer")
    record = one_record(client, auth_headers, seeded_session)
    pending = verify(client, record, officer).json()
    retry = verify(client, record, officer, retry_of=pending["id"])
    assert retry.status_code == 201
    assert retry.json()["retry_of_id"] == pending["id"]

    matched = one_record(client, auth_headers, seeded_session, "900000000001")
    done = verify(client, matched, officer).json()
    assert done["status"] == "SIMULATED_MATCH"
    refused = verify(client, matched, officer, retry_of=done["id"])
    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "RETRY_NOT_ALLOWED"

    # An attempt of a different record is not a valid retry target.
    foreign = verify(client, matched, officer, retry_of=pending["id"])
    assert foreign.status_code == 404
    unknown = verify(client, record, officer, retry_of=str(uuid4()))
    assert unknown.status_code == 404


def test_unavailable_and_timeout_attempts_can_be_retried(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    officer = auth_headers("demo_officer")
    for apaar_id in ("900000000003", "900000000004"):
        record = one_record(client, auth_headers, seeded_session, apaar_id)
        first = verify(client, record, officer).json()
        again = verify(client, record, officer, retry_of=first["id"])
        assert again.status_code == 201, again.text


def test_attempt_limit_per_record_per_day(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
    demo_settings: Settings,
) -> None:
    demo_settings.apaar_max_attempts_per_day = 2
    officer = auth_headers("demo_officer")
    record = one_record(client, auth_headers, seeded_session)
    assert verify(client, record, officer).status_code == 201
    assert verify(client, record, officer).status_code == 201
    limited = verify(client, record, officer)
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RETRY_LIMIT"
    other = one_record(client, auth_headers, seeded_session)
    assert verify(client, other, officer).status_code == 201


def test_purpose_and_consent_are_still_required(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session)
    officer = auth_headers("demo_officer")
    for body in (
        {"purpose": "X"},
        {"consent_ref": "c"},
        {"purpose": "", "consent_ref": "c"},
    ):
        response = client.post(
            f"/api/v1/records/{record}/apaar-verify", headers=officer, json=body
        )
        assert response.status_code == 422
    assert (
        seeded_session.scalar(select(func.count()).select_from(ApaarVerification)) == 0
    )


def test_verification_audit_has_no_identifier(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    record = one_record(client, auth_headers, seeded_session, "900000000001")
    verify(client, record, auth_headers("demo_officer"))
    events = seeded_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "APAAR_VERIFICATION_REQUESTED")
    ).all()
    assert events and all("9000000000" not in str(e.metadata_redacted) for e in events)
