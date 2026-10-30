import csv
import io
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_cases import open_case, record_ids
from test_intake import CEDAR, CEDAR_PROGRAMME, assess, declare, rows_csv
from test_validation import activate_demo, csv_data, run_validation, upload

from app.core.config import Settings
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.cases.models import CaseEvent
from app.modules.integrity.models import IntegrityDecision
from app.modules.integrity.routes import utc_now
from app.modules.submissions.models import StudentRecordVersion, SubmissionBatch
from app.modules.submissions.parsing import HEADERS
from app.modules.verification.models import ApaarVerification
from app.seed import seed_id

Headers = Callable[[str], dict[str, str]]
MAPLE = seed_id("institutions", "maple")
WEIGHTS = {"INFO": 0, "LOW": 1, "MEDIUM": 3, "HIGH": 5}
FAMILY_OF = {
    "DQ": "DATA_QUALITY",
    "IDU": "IDENTITY_UNCERTAINTY",
    "CMP": "COMPLIANCE",
}


def base_url(institution: UUID = CEDAR) -> str:
    return f"/api/v1/integrity/institutions/{institution}"


def configure(application: FastAPI, **changes: Any) -> None:
    application.state.settings = application.state.settings.model_copy(update=changes)


def signals_of(
    client: TestClient,
    headers: dict[str, str],
    institution: UUID = CEDAR,
    **params: str,
) -> dict[str, Any]:
    response = client.get(
        base_url(institution) + "/signals", headers=headers, params=params
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def only(body: dict[str, Any], rule_id: str) -> list[dict[str, Any]]:
    return [s for s in body["signals"] if s["rule_id"] == rule_id]


def make_csv(*rows: dict[str, str]) -> bytes:
    defaults = dict(
        zip(
            HEADERS,
            [
                "DEMO-ONE",
                "Synthetic One",
                "900000000001",
                "2026-27",
                "DEMO-COMP",
                "REGULAR",
                "ACTIVE",
                "2026-08-01",
            ],
            strict=True,
        )
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    for row in rows:
        writer.writerow({**defaults, **row}.values())
    return output.getvalue().encode()


def validated(client: TestClient, headers: dict[str, str], data: bytes) -> str:
    batch = upload(client, headers, data)
    run_validation(client, batch, headers)
    return batch


def decide(
    client: TestClient,
    headers: dict[str, str],
    key: str,
    decision: str = "FALSE_POSITIVE",
    reason: str = "Synthetic officer reason",
    institution: UUID = CEDAR,
) -> Any:
    return client.post(
        base_url(institution) + "/decisions",
        headers=headers,
        json={"signal_key": key, "decision": decision, "reason": reason},
    )


def stale_key(client: TestClient, headers: dict[str, str]) -> str:
    body = signals_of(client, headers)
    return str(only(body, "CMP_STALE_SUBMISSION")[0]["signal_key"])


# ---------------------------------------------------------------- DATA_QUALITY


def test_data_quality_counts_and_clean_batch(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, csv_data())
    # No completed validation run yet: nothing to count, nothing invented.
    assert not [
        s
        for s in signals_of(client, officer)["signals"]
        if s["rule_id"].startswith("DQ_")
    ]
    run_validation(client, batch, admin)
    clean = signals_of(client, officer)
    assert not [s for s in clean["signals"] if s["rule_id"].startswith("DQ_")]

    bad = make_csv(
        {"college_student_id": "A1", "apaar_id": ""},
        {"college_student_id": "A2", "apaar_id": "12AB"},
        {"college_student_id": "A2", "apaar_id": "900000000002"},
        {"college_student_id": "A3", "apaar_id": "900000000005"},
        {"college_student_id": "A4", "apaar_id": "900000000005"},
    )
    run = run_validation(client, upload(client, admin, bad), admin)
    body = signals_of(client, officer)
    missing = only(body, "DQ_MISSING_FIELDS")[0]
    malformed = only(body, "DQ_MALFORMED_APAAR")[0]
    duplicate = only(body, "DQ_DUPLICATE_IDENTIFIERS")[0]
    assert missing["evidence"]["finding_rule_counts"] == {"REQUIRED_FIELD_MISSING": 1}
    assert missing["evidence"]["record_version_total"] == 1
    assert missing["evidence"]["validation_run_id"] == run["id"]
    assert malformed["evidence"]["finding_rule_counts"] == {"INVALID_APAAR_FORMAT": 1}
    assert duplicate["evidence"]["finding_rule_counts"] == {
        "DUPLICATE_COLLEGE_STUDENT_ID": 1,
        "DUPLICATE_IN_BATCH": 1,
    }
    assert duplicate["evidence"]["record_version_total"] == 4
    assert duplicate["calculation"].startswith("2 finding(s) touching 4 record(s)")
    assert {s["family"] for s in (missing, malformed, duplicate)} == {"DATA_QUALITY"}


def test_record_version_ids_are_capped(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    rows = [
        {"college_student_id": f"C{i:03d}", "apaar_id": f"90000000{i:04d}"}
        for i in range(1, 26)
    ]
    for row in rows:
        row["enrollment_date"] = ""
    validated(client, admin, make_csv(*rows))
    missing = only(signals_of(client, officer), "DQ_MISSING_FIELDS")[0]
    assert missing["evidence"]["record_version_total"] == 25
    assert len(missing["evidence"]["record_version_ids"]) == 20


# ------------------------------------------------------ IDENTITY_UNCERTAINTY


@pytest.mark.parametrize(
    "peer_status,severity", [("ACTIVE", "MEDIUM"), ("WITHDRAWN", "INFO")]
)
def test_cross_institution_duplicate_is_a_prompt_without_peer_details(
    client: TestClient, auth_headers: Headers, peer_status: str, severity: str
) -> None:
    maple, cedar = auth_headers("maple_admin"), auth_headers("cedar_admin")
    peer = upload(
        client, maple, csv_data(enrollment_status=peer_status), institution="maple"
    )
    activate_demo(client, peer, maple)
    validated(client, cedar, csv_data())
    body = signals_of(client, cedar)
    found = only(body, "IDU_CROSS_INSTITUTION_DUPLICATE")
    assert len(found) == 1 and found[0]["severity"] == severity
    assert found[0]["family"] == "IDENTITY_UNCERTAINTY"
    assert "transfer" in found[0]["calculation"]
    assert "not a duplicate determination" in found[0]["calculation"]
    assert str(MAPLE) not in str(body) and "maple" not in str(body).lower()
    assert peer not in str(body)


def test_unavailable_is_not_mismatch_and_latest_status_wins(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    ids = [UUID(i) for i in record_ids(seeded_session, batch)]
    actor = seeded_session.scalar(select(User).where(User.demo_alias == "demo_officer"))
    assert actor is not None
    now = datetime.now(UTC)

    def verify(record: UUID, status: str, minutes: int) -> None:
        seeded_session.add(
            ApaarVerification(
                record_version_id=record,
                batch_id=UUID(batch),
                requested_by=actor.id,
                adapter_type="MOCK",
                status=status,
                evidence_json_redacted={},
                consent_ref="synthetic-consent",
                purpose="synthetic test",
                requested_at=now - timedelta(minutes=minutes),
            )
        )

    verify(ids[0], "PENDING", 10)  # superseded by the later status below
    verify(ids[0], "SOURCE_UNAVAILABLE", 5)
    verify(ids[1], "PENDING", 5)
    verify(ids[2], "SIMULATED_MISMATCH", 5)
    seeded_session.flush()
    found = only(signals_of(client, officer), "IDU_VERIFICATION_UNRESOLVED")
    assert len(found) == 3
    by_status = {s["signal_key"].rsplit("|", 1)[1]: s for s in found}
    assert set(by_status) == {"PENDING", "SOURCE_UNAVAILABLE", "SIMULATED_MISMATCH"}
    assert by_status["SOURCE_UNAVAILABLE"]["severity"] == "INFO"
    assert by_status["SIMULATED_MISMATCH"]["severity"] == "MEDIUM"
    assert by_status["PENDING"]["severity"] == "LOW"
    for item in found:
        assert item["title"].startswith("SIMULATED / DEMO DATA")
        assert item["evidence"]["record_version_total"] == 1
    assert "not a mismatch" in by_status["SOURCE_UNAVAILABLE"]["calculation"]


# ------------------------------------------------------------------ COMPLIANCE


@pytest.mark.parametrize("count,fires", [(3, False), (4, True)])
def test_intake_exceeded_boundary(
    client: TestClient, auth_headers: Headers, count: int, fires: bool
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    activate_demo(
        client, upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * count)), admin
    )
    found = only(signals_of(client, officer), "CMP_INTAKE_EXCEEDED")
    assert bool(found) is fires
    if fires:
        assert found[0]["severity"] == "HIGH" and "REGULAR" in found[0]["title"]
        assert "4 > approved 3" in found[0]["calculation"]
        assert len(found) == 1  # other categories are never pooled


def test_missing_declaration_is_not_zero_enrolment(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")]))
    # No current snapshot yet: the rule does not apply.
    assert not only(signals_of(client, officer), "CMP_MISSING_DECLARATION")
    activate_demo(client, batch, admin)
    found = only(signals_of(client, officer), "CMP_MISSING_DECLARATION")
    assert len(found) == 1 and found[0]["severity"] == "LOW"
    assert "not zero enrolment" in found[0]["calculation"]
    assert declare(client, admin, 1).status_code == 201
    assert not only(signals_of(client, officer), "CMP_MISSING_DECLARATION")


@pytest.mark.parametrize("declared,fires", [(3, False), (5, True)])
def test_missing_population_from_assessment(
    client: TestClient, auth_headers: Headers, declared: int, fires: bool
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    assert declare(client, admin, declared).status_code == 201
    assert not only(signals_of(client, officer), "CMP_MISSING_POPULATION")
    assessment = assess(client, batch, admin)
    found = only(signals_of(client, officer), "CMP_MISSING_POPULATION")
    assert bool(found) is fires
    if fires:
        assert found[0]["evidence"]["assessment_id"] == assessment["id"]
        assert "shortfall 2" in found[0]["calculation"]


@pytest.mark.parametrize("mode", ["removed", "changed"])
@pytest.mark.parametrize("threshold,fires", [(0.25, True), (0.26, False)])
def test_unusual_snapshot_change_boundary(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    mode: str,
    threshold: float,
    fires: bool,
) -> None:
    configure(application, integrity_change_ratio_threshold=threshold)
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    spec = [("REGULAR", "ACTIVE")] * 3 + [("NRI", "ACTIVE")]
    activate_demo(client, upload(client, admin, rows_csv(spec)), admin)
    assert not only(signals_of(client, officer), "CMP_UNUSUAL_SNAPSHOT_CHANGE")
    newer = spec[:3] if mode == "removed" else [*spec[:3], ("NRI", "WITHDRAWN")]
    candidate = upload(client, admin, rows_csv(newer))
    found = only(signals_of(client, officer), "CMP_UNUSUAL_SNAPSHOT_CHANGE")
    assert bool(found) is fires
    if fires:
        assert "1 " + mode in found[0]["calculation"]
        assert "25.0% >= threshold 25.0%" in found[0]["calculation"]
        assert "not proof of withdrawal" in found[0]["calculation"]
        assert candidate in found[0]["evidence"]["batch_ids"]
        # After activation the latest activation is compared with its prior.
        activate_demo(client, candidate, admin)
        again = only(signals_of(client, officer), "CMP_UNUSUAL_SNAPSHOT_CHANGE")
        assert len(again) == 1 and candidate in again[0]["evidence"]["batch_ids"]


def add_corrections(session: Session, case_id: str, count: int) -> None:
    for _ in range(count):
        session.add(CaseEvent(case_id=UUID(case_id), action="REQUEST_CORRECTION"))
    session.flush()


def test_repeated_corrections_per_case_and_institution(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    ids = record_ids(seeded_session, upload(client, admin))
    first = open_case(client, officer, ids).json()["id"]
    second = open_case(client, officer, ids).json()["id"]
    add_corrections(seeded_session, first, 1)
    assert not only(signals_of(client, officer), "CMP_REPEATED_CORRECTIONS")
    # Two requests in total, but no single case reaches the threshold.
    add_corrections(seeded_session, second, 1)
    found = only(signals_of(client, officer), "CMP_REPEATED_CORRECTIONS")
    assert [s["signal_key"] for s in found] == ["CMP_REPEATED_CORRECTIONS|institution"]
    assert set(found[0]["evidence"]["case_ids"]) == {first, second}
    # Once one case reaches the threshold only that case is flagged (no double count).
    add_corrections(seeded_session, first, 1)
    found = only(signals_of(client, officer), "CMP_REPEATED_CORRECTIONS")
    assert len(found) == 1 and found[0]["evidence"]["case_ids"] == [first]
    assert found[0]["evidence"]["finding_rule_counts"] == {"REQUEST_CORRECTION": 2}


def test_overdue_cases_and_escalation(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    ids = record_ids(seeded_session, upload(client, admin))
    now = datetime.now(UTC)

    def case(offset: timedelta) -> str:
        return str(
            open_case(client, officer, ids, due_at=(now + offset).isoformat()).json()[
                "id"
            ]
        )

    case(timedelta(days=1))
    assert not only(signals_of(client, officer), "CMP_OVERDUE_CASES")
    late = case(-timedelta(days=1))
    found = only(signals_of(client, officer), "CMP_OVERDUE_CASES")
    assert found[0]["severity"] == "MEDIUM" and found[0]["evidence"]["case_ids"] == [
        late
    ]
    assert found[0]["calculation"].startswith("1 open case(s) past due, 0 ")
    case(-timedelta(days=8))
    found = only(signals_of(client, officer), "CMP_OVERDUE_CASES")
    assert found[0]["severity"] == "HIGH" and len(found[0]["evidence"]["case_ids"]) == 2


def pin_clock(application: FastAPI, moment: datetime) -> None:
    application.dependency_overrides[utc_now] = lambda: moment


def activated_at(session: Session, batch: str) -> datetime:
    stamp = session.scalar(
        select(SubmissionBatch.activated_at).where(SubmissionBatch.id == UUID(batch))
    )
    assert stamp is not None
    return stamp


def stale_for_programme(client: TestClient, headers: dict[str, str]) -> list[Any]:
    return [
        s
        for s in only(signals_of(client, headers), "CMP_STALE_SUBMISSION")
        if s["programme_id"] == str(CEDAR_PROGRAMME)
    ]


def test_stale_submission_boundary(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    never = stale_for_programme(client, officer)
    assert len(never) == 1 and "no activated snapshot" in never[0]["calculation"]
    assert "not zero enrolment" in never[0]["calculation"]
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")]))
    activate_demo(client, batch, admin)
    assert stale_for_programme(client, officer) == []

    stamp = activated_at(seeded_session, batch)
    pin_clock(application, stamp + timedelta(days=90))  # exactly at the limit
    assert stale_for_programme(client, officer) == []
    pin_clock(application, stamp + timedelta(days=90, minutes=5))
    old = stale_for_programme(client, officer)
    assert len(old) == 1 and "90 day(s) old" in old[0]["calculation"]
    assert old[0]["evidence"]["batch_ids"] == [batch]


def test_stale_days_setting_controls_threshold(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")]))
    activate_demo(client, batch, admin)
    pin_clock(application, activated_at(seeded_session, batch) + timedelta(days=10))
    assert stale_for_programme(client, officer) == []
    configure(application, integrity_stale_days=9)
    assert len(stale_for_programme(client, officer)) == 1


# ----------------------------------------------------------------- scoring


def test_families_scores_and_bands(
    client: TestClient, application: FastAPI, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    rows = [
        {"college_student_id": f"S{i}", "apaar_id": f"90000000000{i}"}
        for i in range(1, 5)
    ]
    rows[0]["apaar_id"] = ""
    activate_demo(client, upload(client, admin, make_csv(*rows)), admin)
    body = signals_of(client, officer)
    assert body["score"]["formula"] == (
        "sum over non-dismissed signals of severity weight"
    )
    assert body["score"]["severity_weights"] == WEIGHTS
    for item in body["signals"]:
        assert item["family"] == FAMILY_OF[item["rule_id"].split("_")[0]]
    components = {c["family"]: c for c in body["score"]["components"]}
    assert list(components) == ["DATA_QUALITY", "IDENTITY_UNCERTAINTY", "COMPLIANCE"]
    total = 0
    for family, component in components.items():
        members = [s for s in body["signals"] if s["family"] == family]
        expected = sum(WEIGHTS[s["severity"]] for s in members)
        assert component["signal_count"] == component["active_count"] == len(members)
        assert component["weighted_points"] == expected
        total += expected
    assert components["IDENTITY_UNCERTAINTY"]["signal_count"] == 0
    assert components["IDENTITY_UNCERTAINTY"]["max_severity"] is None
    assert components["DATA_QUALITY"]["max_severity"] == "MEDIUM"
    assert components["COMPLIANCE"]["max_severity"] == "HIGH"
    assert body["score"]["total_points"] == total
    assert total >= 3 + 5 + 1  # missing field + intake exceeded + no declaration

    def band(medium: int, high: int) -> str:
        configure(
            application,
            integrity_band_medium_points=medium,
            integrity_band_high_points=high,
        )
        return str(signals_of(client, officer)["score"]["band"])

    assert band(total, total + 1) == "MEDIUM"  # boundary: points == threshold
    assert band(total + 1, total + 2) == "LOW"
    assert band(total - 1, total) == "HIGH"
    assert signals_of(client, officer)["score"]["band_thresholds"] == {
        "MEDIUM": total - 1,
        "HIGH": total,
    }


def test_dismissal_keeps_listing_but_removes_points_and_latest_wins(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    key = stale_key(client, officer)
    before = signals_of(client, officer)
    item = next(s for s in before["signals"] if s["signal_key"] == key)
    assert item["decision"] is None and item["dismissed"] is False

    created = decide(client, officer, key, "FALSE_POSITIVE")
    assert created.status_code == 201, created.text
    after = signals_of(client, officer)
    item = next(s for s in after["signals"] if s["signal_key"] == key)
    assert item["dismissed"] is True and item["decision"] == "FALSE_POSITIVE"
    assert len(after["signals"]) == len(before["signals"])
    assert after["score"]["total_points"] == before["score"]["total_points"] - 1
    compliance = {c["family"]: c for c in after["score"]["components"]}["COMPLIANCE"]
    old = {c["family"]: c for c in before["score"]["components"]}["COMPLIANCE"]
    assert compliance["signal_count"] == old["signal_count"]
    assert compliance["active_count"] == old["active_count"] - 1

    # Latest decision wins; other decisions never dismiss.
    for decision in ("CONFIRMED_CONCERN", "NEEDS_FOLLOW_UP"):
        assert decide(client, officer, key, decision).status_code == 201
        now = signals_of(client, officer)
        item = next(s for s in now["signals"] if s["signal_key"] == key)
        assert item["decision"] == decision and item["dismissed"] is False
        assert now["score"]["total_points"] == before["score"]["total_points"]
    history = client.get(
        base_url() + "/decisions", headers=officer, params={"signal_key": key}
    ).json()
    assert [d["decision"] for d in history["data"]] == [
        "NEEDS_FOLLOW_UP",
        "CONFIRMED_CONCERN",
        "FALSE_POSITIVE",
    ]
    assert history["pagination"]["total"] == 3
    assert all(d["reason"] == "Synthetic officer reason" for d in history["data"])
    # Decisions are scoped to the institution.
    other = client.get(base_url(MAPLE) + "/decisions", headers=officer).json()
    assert other["data"] == []


def test_decisions_are_append_only(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    key = stale_key(client, officer)
    assert decide(client, officer, key).status_code == 201
    row = seeded_session.scalars(select(IntegrityDecision)).one()
    with pytest.raises(DBAPIError, match="append-only"), seeded_session.begin_nested():
        seeded_session.execute(
            text("UPDATE integrity_decisions SET reason = 'edited reason'")
        )
    with pytest.raises(DBAPIError, match="append-only"), seeded_session.begin_nested():
        seeded_session.execute(text("DELETE FROM integrity_decisions"))
    seeded_session.refresh(row)
    assert row.reason == "Synthetic officer reason"


def test_decision_validation_and_unknown_signal(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    key = stale_key(client, officer)
    unknown = decide(client, officer, "CMP_STALE_SUBMISSION|not-a-signal")
    assert unknown.status_code == 422
    assert unknown.json()["error"]["code"] == "UNKNOWN_SIGNAL"
    # A key computed for another institution is not a signal of this one.
    cross = decide(client, officer, key, institution=MAPLE)
    assert (
        cross.status_code == 422 and cross.json()["error"]["code"] == "UNKNOWN_SIGNAL"
    )
    for bad in (
        {"signal_key": key, "decision": "FALSE_POSITIVE", "reason": "ab"},
        {"signal_key": key, "decision": "FALSE_POSITIVE", "reason": "x" * 501},
        {"signal_key": key, "decision": "FRAUD", "reason": "valid reason"},
        {"signal_key": key, "decision": "FALSE_POSITIVE"},
        {"signal_key": "", "decision": "FALSE_POSITIVE", "reason": "valid reason"},
        {"signal_key": key, "decision": "FALSE_POSITIVE", "reason": "ok ok", "x": 1},
    ):
        response = client.post(base_url() + "/decisions", headers=officer, json=bad)
        assert response.status_code == 422, bad
    assert seeded_session.scalars(select(IntegrityDecision)).all() == []
    assert decide(client, officer, key, reason="  abc  ").json()["reason"] == "abc"


def test_decision_audit_event_is_minimal(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    key = stale_key(client, officer)
    created = decide(client, officer, key, "NEEDS_FOLLOW_UP", "Private officer note")
    event = seeded_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "INTEGRITY_DECISION_RECORDED")
    ).one()
    assert str(event.entity_id) == created.json()["id"]
    assert event.institution_id == CEDAR and event.actor_id is not None
    assert event.metadata_redacted["decision"] == "NEEDS_FOLLOW_UP"
    assert event.metadata_redacted["rule_id"] == "CMP_STALE_SUBMISSION"
    assert key not in str(event.metadata_redacted)
    assert "Private officer note" not in str(event.metadata_redacted)


# ------------------------------------------------------- roles and scoping


def test_signals_role_matrix(client: TestClient, auth_headers: Headers) -> None:
    url = base_url() + "/signals"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth_headers("demo_manager")).status_code == 403
    assert client.get(url, headers=auth_headers("demo_officer")).status_code == 200
    assert client.get(url, headers=auth_headers("cedar_admin")).status_code == 200
    maple = base_url(MAPLE) + "/signals"
    assert client.get(maple, headers=auth_headers("demo_officer")).status_code == 200
    denied = client.get(maple, headers=auth_headers("cedar_admin"))
    assert denied.status_code == 404
    missing = client.get(
        base_url(UUID(int=7)) + "/signals", headers=auth_headers("cedar_admin")
    )
    # Indistinguishable from a nonexistent institution.
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == denied.json()["error"]["code"]
    assert missing.json()["error"]["message"] == denied.json()["error"]["message"]
    unknown = client.get(
        base_url(UUID(int=7)) + "/signals", headers=auth_headers("demo_officer")
    )
    assert unknown.status_code == 404
    foreign = client.get(
        url,
        headers=auth_headers("demo_officer"),
        params={"programme_id": str(seed_id("programmes", "maple/DEMO-COMP"))},
    )
    assert foreign.status_code == 404


def test_decision_endpoints_are_officer_only(
    client: TestClient, auth_headers: Headers
) -> None:
    key = stale_key(client, auth_headers("demo_officer"))
    for alias in ("cedar_admin", "demo_manager", "maple_admin"):
        headers = auth_headers(alias)
        assert decide(client, headers, key).status_code == 403, alias
        history = client.get(base_url() + "/decisions", headers=headers)
        assert history.status_code == 403, alias
    assert client.get(base_url() + "/decisions").status_code == 401
    assert decide(client, auth_headers("demo_officer"), key).status_code == 201


def test_overview_is_aggregate_for_officer_and_manager(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    manager = auth_headers("demo_manager")
    activate_demo(
        client, upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 4)), admin
    )
    url = "/api/v1/integrity/overview"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=admin).status_code == 403
    responses = [client.get(url, headers=h) for h in (officer, manager)]
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json()["data"] == responses[1].json()["data"]
    body = responses[1].json()
    for forbidden in (
        "record_version_ids",
        "evidence",
        "signal_key",
        "batch_ids",
        "case_ids",
        "validation_run_id",
        "calculation",
    ):
        assert forbidden not in responses[1].text
    points = [item["score"]["total_points"] for item in body["data"]]
    assert points == sorted(points, reverse=True) and len(points) >= 2
    assert body["data"][0]["institution_id"] == str(CEDAR)
    assert body["data"][0]["active_count"] == body["data"][0]["signal_count"]
    assert "not fraud" in body["disclaimer"]

    page = client.get(url, headers=manager, params={"page_size": 1, "page": 2}).json()
    assert len(page["data"]) == 1 and page["pagination"]["total"] == len(points)
    assert page["data"][0]["institution_id"] == body["data"][1]["institution_id"]
    bands = {item["score"]["band"] for item in body["data"]}
    for band in ("LOW", "MEDIUM", "HIGH"):
        filtered = client.get(url, headers=officer, params={"band": band}).json()
        assert {i["score"]["band"] for i in filtered["data"]} <= {band}
        assert (len(filtered["data"]) > 0) == (band in bands)
    nothing = client.get(url, headers=officer, params={"academic_year": "2025-26"})
    assert nothing.status_code == 200
    # No 2025-26 submissions: only programme-level staleness prompts remain.
    assert all(
        i["score"]["components"][2]["signal_count"] == i["signal_count"]
        for i in nothing.json()["data"]
    )
    assert client.get(url, headers=officer, params={"band": "X"}).status_code == 422


def test_filters_narrow_scope_based_signals(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    activate_demo(
        client, upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 4)), admin
    )
    assert only(
        signals_of(client, officer, academic_year="2026-27"), "CMP_INTAKE_EXCEEDED"
    )
    assert not only(
        signals_of(client, officer, academic_year="2025-26"), "CMP_INTAKE_EXCEEDED"
    )
    scoped = signals_of(client, officer, programme_id=str(CEDAR_PROGRAMME))
    assert only(scoped, "CMP_INTAKE_EXCEEDED")
    # Keys do not depend on the filter, so decisions keep matching.
    full = only(signals_of(client, officer), "CMP_INTAKE_EXCEEDED")[0]["signal_key"]
    assert only(scoped, "CMP_INTAKE_EXCEEDED")[0]["signal_key"] == full


def test_disclaimer_and_no_identifying_values(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    rows = [
        {"college_student_id": f"PRIV-S{i}", "student_name": f"Private Name {i}"}
        for i in range(1, 5)
    ]
    rows[0]["apaar_id"] = "900000000001"
    rows[1]["apaar_id"] = "900000000001"
    rows[2]["apaar_id"] = "BADVALUE12"
    rows[3]["apaar_id"] = ""
    batch = validated(client, admin, make_csv(*rows))
    ids = record_ids(seeded_session, batch)
    open_case(client, officer, ids)
    key = stale_key(client, officer)
    responses = [
        client.get(base_url() + "/signals", headers=officer),
        client.get(base_url() + "/signals", headers=admin),
        client.get("/api/v1/integrity/overview", headers=auth_headers("demo_manager")),
        decide(client, officer, key),
        client.get(base_url() + "/decisions", headers=officer),
    ]
    for response in responses:
        assert response.status_code in {200, 201}
        for secret in ("900000000001", "BADVALUE12", "Private Name", "PRIV-S"):
            assert secret not in response.text
    for response in responses[:3]:
        assert "not fraud" in response.json()["disclaimer"]
    assert "not fraud" in responses[3].json()["disclaimer"]
    assert "not fraud" in responses[4].json()["data"][0]["disclaimer"]
    body = responses[0].json()
    assert body["source_label"] == "DEMO"
    assert only(body, "DQ_MALFORMED_APAAR") and only(body, "DQ_DUPLICATE_IDENTIFIERS")
    # Record references are ids only.
    known = {str(r.id) for r in seeded_session.scalars(select(StudentRecordVersion))}
    for item in body["signals"]:
        assert set(item["evidence"]["record_version_ids"]) <= known


# ------------------------------------------------------------ configuration


def test_integrity_settings_defaults_and_validation(settings: Settings) -> None:
    assert settings.integrity_change_ratio_threshold == 0.25
    assert settings.integrity_repeated_corrections_threshold == 2
    assert settings.integrity_stale_days == 90
    assert settings.integrity_severity_weights == WEIGHTS
    base = SecretStr("postgresql+psycopg://u@localhost/d")
    for bad in (
        {"integrity_change_ratio_threshold": 0},
        {"integrity_change_ratio_threshold": 1.5},
        {"integrity_repeated_corrections_threshold": 0},
        {"integrity_stale_days": 0},
        {"integrity_severity_weights": {"INFO": 0, "LOW": 1}},
        {"integrity_severity_weights": {**WEIGHTS, "HIGH": -1}},
        {"integrity_severity_weights": {**WEIGHTS, "CRITICAL": 9}},
        {"integrity_band_medium_points": 5, "integrity_band_high_points": 5},
    ):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, database_url=base, **bad)
