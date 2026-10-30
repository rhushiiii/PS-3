import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_activation import activate_http, review
from test_cases import open_case
from test_validation import activate_demo, csv_data, upload

from app.modules.audit.models import AuditEvent
from app.modules.auth.models import Role, User
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch
from app.seed import seed_id

SAMPLES = Path(__file__).resolve().parents[3] / "samples"
RAW_APAAR = ("900000000001", "900000000002", "900000000003")
Headers = Callable[[str], dict[str, str]]


def version_id(session: Session, batch_id: str, student_id: str) -> str:
    record = session.scalar(
        select(StudentRecordVersion).where(
            StudentRecordVersion.batch_id == batch_id,
            StudentRecordVersion.college_student_id == student_id,
        )
    )
    assert record is not None
    return str(record.id)


def replacement_flow(
    client: TestClient, auth_headers: Headers, session: Session
) -> tuple[str, str, dict[str, str]]:
    """Initial snapshot activated, then a replacement activated over it."""
    headers = auth_headers("cedar_admin")
    initial = upload(
        client, headers, (SAMPLES / "synthetic_snapshot_initial.csv").read_bytes()
    )
    activate_http(client, initial, review(client, initial, headers), headers)
    replacement = upload(
        client, headers, (SAMPLES / "synthetic_snapshot_replacement.csv").read_bytes()
    )
    activate_http(client, replacement, review(client, replacement, headers), headers)
    # The test session is one transaction, so now() gives every batch the same
    # received_at; real uploads arrive in separate transactions.
    for offset, batch_id in enumerate((initial, replacement)):
        batch = session.get(SubmissionBatch, UUID(batch_id))
        assert batch is not None
        batch.received_at = datetime(2026, 8, 1, tzinfo=UTC) + timedelta(hours=offset)
    session.commit()
    return initial, replacement, headers


def listed(client: TestClient, headers: dict[str, str], query: str = "") -> Any:
    response = client.get(f"/api/v1/records?{query}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_unauthenticated_and_role_matrix(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin = auth_headers("cedar_admin")
    identifier = upload(client, admin)
    activate_demo(client, identifier, admin)
    record = version_id(seeded_session, identifier, "DEMO-ONE")
    for path in ("/api/v1/records", f"/api/v1/records/{record}"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=admin).status_code == 200
        assert client.get(path, headers=auth_headers("demo_officer")).status_code == 200
        assert client.get(path, headers=auth_headers("demo_manager")).status_code == 403

    # Another institution's admin: detail is 404 (no existence leak); list is empty.
    maple = auth_headers("maple_admin")
    assert client.get(f"/api/v1/records/{record}", headers=maple).status_code == 404
    assert listed(client, maple)["data"] == []
    unknown = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/records/{unknown}", headers=maple).status_code == 404
    # Authorized verifier has no registry access.
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    user.role = Role.AUTHORIZED_VERIFIER
    seeded_session.commit()
    assert client.get("/api/v1/records", headers=admin).status_code == 403
    assert client.get(f"/api/v1/records/{record}", headers=admin).status_code == 403


def test_filters_and_institution_scoping(
    client: TestClient, auth_headers: Headers
) -> None:
    cedar, maple = auth_headers("cedar_admin"), auth_headers("maple_admin")
    officer = auth_headers("demo_officer")
    activate_demo(client, upload(client, cedar), cedar)
    activate_demo(
        client,
        upload(client, maple, csv_data(college_student_id="MAPLE-1"), "maple"),
        maple,
    )
    cedar_id = str(seed_id("institutions", "cedar"))
    maple_id = str(seed_id("institutions", "maple"))

    assert listed(client, officer)["pagination"]["total"] == 2
    own = listed(client, officer, f"institution_id={cedar_id}")
    assert [row["college_student_id"] for row in own["data"]] == ["DEMO-ONE"]
    assert own["data"][0]["institution_name"]
    # Admins are forced to their own institution; naming another is a 404.
    assert listed(client, maple)["data"][0]["college_student_id"] == "MAPLE-1"
    other = client.get(f"/api/v1/records?institution_id={cedar_id}", headers=maple)
    assert other.status_code == 404
    assert (
        listed(client, maple, f"institution_id={maple_id}")["pagination"]["total"] == 1
    )

    programme = own["data"][0]["programme_id"]
    assert (
        listed(client, officer, f"programme_id={programme}")["pagination"]["total"] == 1
    )
    unknown = "00000000-0000-0000-0000-000000000000"
    assert (
        client.get(f"/api/v1/records?programme_id={unknown}", headers=officer)
    ).status_code == 404
    # A programme of another institution is invisible to an admin.
    assert (
        client.get(f"/api/v1/records?programme_id={programme}", headers=maple)
    ).status_code == 404

    assert listed(client, officer, "academic_year=2026-27")["pagination"]["total"] == 2
    assert listed(client, officer, "academic_year=2025-26")["data"] == []
    assert (
        listed(client, officer, "enrollment_status=ACTIVE")["pagination"]["total"] == 2
    )
    assert listed(client, officer, "enrollment_status=WITHDRAWN")["data"] == []
    for bad in ("enrollment_status=BOGUS", "validation_status=BOGUS", "page_size=0"):
        assert client.get(f"/api/v1/records?{bad}", headers=officer).status_code == 422


def test_validation_status_filter_and_row_shape(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    _, replacement, headers = replacement_flow(client, auth_headers, seeded_session)
    rows = {r["college_student_id"]: r for r in listed(client, headers)["data"]}
    assert set(rows) == {"DEMO-001", "DEMO-002"}
    assert rows["DEMO-002"]["validation_status"] == "INCOMPLETE"
    assert rows["DEMO-002"]["enrollment_status"] == "WITHDRAWN"
    assert rows["DEMO-001"]["validation_status"] in {"VALID", "FLAGGED"}
    assert rows["DEMO-001"]["category"] == "NRI"
    assert rows["DEMO-001"]["masked_apaar"] == "********0001"
    assert rows["DEMO-001"]["batch_id"] == replacement
    assert rows["DEMO-001"]["is_current"] is True
    assert rows["DEMO-001"]["snapshot_state"] == "CURRENT"
    assert rows["DEMO-001"]["source_label"] == "DEMO"
    incomplete = listed(client, headers, "validation_status=INCOMPLETE")
    assert [r["college_student_id"] for r in incomplete["data"]] == ["DEMO-002"]
    other = rows["DEMO-001"]["validation_status"]
    flagged = listed(client, headers, "validation_status=FLAGGED")["data"]
    valid = listed(client, headers, "validation_status=VALID")["data"]
    assert [r["college_student_id"] for r in flagged + valid] == ["DEMO-001"]
    assert (flagged or valid)[0]["validation_status"] == other


def test_q_matches_student_id_prefix_and_name_but_never_apaar(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    _, _, headers = replacement_flow(client, auth_headers, seeded_session)
    activated = {
        r["college_student_id"] for r in listed(client, headers, "q=demo-0")["data"]
    }
    assert activated == {"DEMO-001", "DEMO-002"}  # case-insensitive prefix
    assert listed(client, headers, "q=-001")["data"] == []  # not a substring match
    by_name = listed(client, headers, "q=SYNTHETIC%20oNe")["data"]
    assert [r["college_student_id"] for r in by_name] == ["DEMO-001"]
    assert listed(client, headers, "q=%25")["data"] == []  # wildcards are literal
    # APAAR search is unsupported: full, partial and masked forms never match.
    for needle in ("900000000001", "9000000000", "0001", "********0001"):
        assert listed(client, headers, f"q={needle}")["data"] == []


def test_include_candidates_pagination_and_ordering(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    initial, replacement, headers = replacement_flow(
        client, auth_headers, seeded_session
    )
    candidate = upload(
        client, headers, csv_data(college_student_id="DEMO-009", student_name="Cand")
    )
    default = listed(client, headers)
    assert default["pagination"]["total"] == 2
    assert {r["batch_id"] for r in default["data"]} == {replacement}
    # Superseded versions are never listed, with or without candidates.
    with_candidates = listed(client, headers, "include_candidates=true")
    assert with_candidates["pagination"]["total"] == 3
    states = {
        r["college_student_id"]: r["snapshot_state"] for r in with_candidates["data"]
    }
    assert states == {
        "DEMO-001": "CURRENT",
        "DEMO-002": "CURRENT",
        "DEMO-009": "CANDIDATE",
    }
    cand_row = with_candidates["data"][-1]
    assert cand_row["batch_id"] == candidate and cand_row["is_current"] is False
    assert cand_row["validation_status"] is None  # never validated
    assert initial not in {r["batch_id"] for r in with_candidates["data"]}

    first = listed(client, headers, "include_candidates=true&page=1&page_size=2")
    second = listed(client, headers, "include_candidates=true&page=2&page_size=2")
    assert first["pagination"] == {"page": 1, "page_size": 2, "total": 3}
    assert [r["college_student_id"] for r in first["data"]] == ["DEMO-001", "DEMO-002"]
    assert [r["college_student_id"] for r in second["data"]] == ["DEMO-009"]
    assert listed(client, headers, "page=9")["data"] == []


def test_detail_provenance_diff_and_omission_across_replacement(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    initial, replacement, headers = replacement_flow(
        client, auth_headers, seeded_session
    )
    old_three = version_id(seeded_session, initial, "DEMO-003")
    omitted = client.get(f"/api/v1/records/{old_three}", headers=headers).json()
    assert omitted["provenance"]["snapshot_state"] == "SUPERSEDED"
    assert omitted["provenance"]["superseded_by_batch_id"] == replacement
    assert omitted["provenance"]["source"] == "CSV_UPLOAD"
    assert omitted["provenance"]["activated_at"] is not None
    assert omitted["is_current"] is False
    assert omitted["snapshot_presence"] == "NOT_IN_LATEST_SNAPSHOT"
    assert "not proof" in omitted["presence_note"]
    assert omitted["enrollment_status"] == "ACTIVE"  # stored value, not inferred
    assert len(omitted["history"]) == 1 and omitted["history"][0]["changes"] == []

    old_two = version_id(seeded_session, initial, "DEMO-002")
    new_two = version_id(seeded_session, replacement, "DEMO-002")
    detail = client.get(f"/api/v1/records/{new_two}", headers=headers).json()
    assert detail["provenance"]["snapshot_state"] == "CURRENT"
    assert detail["provenance"]["superseded_by_batch_id"] is None
    assert detail["snapshot_presence"] == "IN_LATEST_SNAPSHOT"
    history = detail["history"]
    assert [h["record_version_id"] for h in history] == [old_two, new_two]
    assert [h["snapshot_state"] for h in history] == ["SUPERSEDED", "CURRENT"]
    assert history[0]["apaar_changed"] is None and history[0]["changes"] == []
    assert history[1]["apaar_changed"] is True
    changes = {c["field"]: (c["previous"], c["current"]) for c in history[1]["changes"]}
    assert changes == {
        "student_name": ("Synthetic Two", ""),
        "enrollment_status": ("ACTIVE", "WITHDRAWN"),
        "enrollment_date": ("2026-08-01", None),
    }
    # An unchanged APAAR reports False without exposing any value.
    one = version_id(seeded_session, replacement, "DEMO-001")
    one_history = client.get(f"/api/v1/records/{one}", headers=headers).json()[
        "history"
    ]
    assert one_history[1]["apaar_changed"] is False
    assert {c["field"] for c in one_history[1]["changes"]} == {"category"}
    # A superseded version reached directly is also readable.
    old = client.get(f"/api/v1/records/{old_two}", headers=headers).json()
    assert old["snapshot_presence"] == "IN_LATEST_SNAPSHOT"
    assert old["provenance"]["superseded_by_batch_id"] == replacement


def test_candidate_detail_state(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    headers = auth_headers("cedar_admin")
    candidate = upload(client, headers)
    detail = client.get(
        f"/api/v1/records/{version_id(seeded_session, candidate, 'DEMO-ONE')}",
        headers=headers,
    ).json()
    assert detail["provenance"]["snapshot_state"] == "CANDIDATE"
    assert detail["provenance"]["activated_at"] is None
    assert detail["snapshot_presence"] == "NOT_APPLICABLE"
    assert detail["validation_status"] is None and detail["findings"] == []
    assert detail["verification"] is None and detail["cases"] == []


def test_findings_verification_and_cases_linked_to_record(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    initial, replacement, headers = replacement_flow(
        client, auth_headers, seeded_session
    )
    officer = auth_headers("demo_officer")
    incomplete = version_id(seeded_session, replacement, "DEMO-002")
    clean = version_id(seeded_session, replacement, "DEMO-001")
    detail = client.get(f"/api/v1/records/{incomplete}", headers=headers).json()
    assert detail["validation_status"] == "INCOMPLETE"
    rules = {f["rule_code"] for f in detail["findings"]}
    assert "REQUIRED_FIELD_MISSING" in rules
    for finding in detail["findings"]:
        assert finding["batch_id"] == replacement
        assert finding["severity"] in {"ERROR", "WARNING", "INFO"}
        assert finding["classification"] in {"ACTIVATION_BLOCKING", "REVIEWABLE"}
    other_ids = {
        f["record_version_id"]
        for f in detail["findings"]
        if f["record_version_id"] is not None
    }
    assert other_ids <= {incomplete}
    findings_clean = client.get(f"/api/v1/records/{clean}", headers=headers).json()
    assert "REQUIRED_FIELD_MISSING" not in {
        f["rule_code"] for f in findings_clean["findings"]
    }

    # Verification summary: latest simulated result with provenance, never a value.
    assert detail["verification"] is None
    sent = client.post(
        f"/api/v1/records/{clean}/apaar-verify",
        headers=officer,
        json={"purpose": "AICTE_CASE_REVIEW", "consent_ref": "consent-demo-1"},
    )
    assert sent.status_code == 201, sent.text
    summary = client.get(f"/api/v1/records/{clean}", headers=headers).json()
    verification = summary["verification"]
    assert verification["status"] == sent.json()["status"]
    assert verification["source_type"] == "SIMULATED"
    assert "SIMULATED" in verification["provenance_label"]
    assert verification["requested_at"] and verification["completed_at"]

    # Related cases.
    assert summary["cases"] == []
    created = open_case(client, officer, [clean])
    assert created.status_code == 201, created.text
    cases = client.get(f"/api/v1/records/{clean}", headers=headers).json()["cases"]
    assert len(cases) == 1
    assert cases[0]["id"] == created.json()["id"]
    assert cases[0]["status"] == "OPEN"
    assert {"priority", "severity", "is_overdue", "opened_at"} <= set(cases[0])
    assert cases[0]["is_overdue"] is False
    assert (
        client.get(f"/api/v1/records/{incomplete}", headers=headers).json()["cases"]
        == []
    )


def test_detail_writes_audit_and_apaar_never_appears(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    initial, replacement, headers = replacement_flow(
        client, auth_headers, seeded_session
    )
    officer = auth_headers("demo_officer")
    old_one = version_id(seeded_session, initial, "DEMO-001")
    new_one = version_id(seeded_session, replacement, "DEMO-001")
    client.post(
        f"/api/v1/records/{new_one}/apaar-verify",
        headers=officer,
        json={"purpose": "AICTE_CASE_REVIEW", "consent_ref": "consent-demo-1"},
    )
    open_case(client, officer, [new_one])

    def viewed() -> list[AuditEvent]:
        return list(
            seeded_session.scalars(
                select(AuditEvent).where(AuditEvent.action == "RECORD_VIEWED")
            )
        )

    listed(client, headers)
    listed(client, officer, "include_candidates=true&q=demo")
    assert viewed() == []  # list calls are not audited

    bodies = [
        client.get("/api/v1/records?include_candidates=true", headers=officer).text,
        client.get(f"/api/v1/records/{new_one}", headers=officer).text,
        client.get(f"/api/v1/records/{old_one}", headers=headers).text,
    ]
    for body in bodies:
        for raw in RAW_APAAR:
            assert raw not in body
    events = viewed()
    assert len(events) == 2
    officer_event = next(
        e for e in events if e.entity_id.hex == new_one.replace("-", "")
    )
    assert officer_event.actor_id == seed_id("users", "demo_officer")
    assert officer_event.institution_id == seed_id("institutions", "cedar")
    assert officer_event.entity_type == "student_record_versions"
    for event in events:
        text = json.dumps(event.metadata_redacted)
        for forbidden in (*RAW_APAAR, "Synthetic", "DEMO-"):
            assert forbidden not in text
    # Denied reads leave no audit event.
    count = len(events)
    assert (
        client.get(
            f"/api/v1/records/{new_one}", headers=auth_headers("maple_admin")
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/records/{new_one}", headers=auth_headers("demo_manager")
        ).status_code
        == 403
    )
    assert len(viewed()) == count


@pytest.mark.parametrize("path", ["/api/v1/records", "/api/v1/records/not-a-uuid"])
def test_malformed_requests_are_rejected(
    client: TestClient, auth_headers: Headers, path: str
) -> None:
    headers = auth_headers("demo_officer")
    if path.endswith("not-a-uuid"):
        assert client.get(path, headers=headers).status_code == 422
    else:
        assert client.get(f"{path}?q={'x' * 101}", headers=headers).status_code == 422
