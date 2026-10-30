import csv
import io
import json
import re
from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_activation import SAMPLES, activate_http, review
from test_validation import run_validation, upload

from app.modules.audit.models import AuditEvent
from app.modules.auth.models import Role, User
from app.modules.intake.models import (
    IntakeAssessment,
    IntakeDeclaration,
    IntakeRuleChange,
)
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.parsing import HEADERS
from app.seed import seed_id

Headers = Callable[[str], dict[str, str]]
YEAR = "2026-27"
CEDAR = seed_id("institutions", "cedar")
CEDAR_PROGRAMME = seed_id("programmes", "cedar/DEMO-COMP")


def rows_csv(
    spec: list[tuple[str, str]], year: str = YEAR, status: str = "ACTIVE"
) -> bytes:
    """spec = [(category, status)]; synthetic ids and APAAR-like tokens only."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    for index, (category, row_status) in enumerate(spec, start=1):
        writer.writerow(
            [
                f"DEMO-I{index:03d}",
                f"Synthetic {index}",
                f"9000000{index:05d}",
                year,
                "DEMO-COMP",
                category,
                row_status or status,
                "2026-08-01",
            ]
        )
    return output.getvalue().encode()


def assess(
    client: TestClient, batch: str, headers: dict[str, str], expected: int = 201
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/submissions/{batch}/intake-assessments", headers=headers
    )
    assert response.status_code == expected, response.text
    return dict(response.json())


def by_category(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["category"]: item for item in result["categories"]}


def rule_id(
    client: TestClient,
    headers: dict[str, str],
    category: str,
    institution: str = "cedar",
) -> str:
    identifier = seed_id("institutions", institution)
    programme = seed_id("programmes", f"{institution}/DEMO-COMP")
    data = client.get(
        f"/api/v1/institutions/{identifier}/intake",
        params={"academic_year": YEAR, "programme_id": str(programme)},
        headers=headers,
    ).json()["data"]
    return str(next(rule["id"] for rule in data if rule["category"] == category))


def patch_rule(
    client: TestClient,
    headers: dict[str, str],
    rule: str,
    seats: int,
    reason: str = "Synthetic DEMO adjustment",
    institution: UUID = CEDAR,
) -> Any:
    return client.patch(
        f"/api/v1/institutions/{institution}/intake/{rule}",
        headers=headers,
        json={"approved_seats": seats, "reason": reason},
    )


def declare(
    client: TestClient, headers: dict[str, str], total: int, institution: UUID = CEDAR
) -> Any:
    return client.post(
        f"/api/v1/institutions/{institution}/declarations",
        headers=headers,
        json={
            "programme_id": str(CEDAR_PROGRAMME),
            "academic_year": YEAR,
            "declared_total": total,
            "basis": "Synthetic DEMO admission register total",
        },
    )


def test_boundary_count_equal_cap_then_cap_plus_one(
    client: TestClient, auth_headers: Headers
) -> None:
    admin = auth_headers("cedar_admin")
    equal = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    result = assess(client, equal, admin)["result"]
    regular = by_category(result)["REGULAR"]
    assert result["source_label"] == "DEMO" and "not official" in result["notice"]
    assert regular["approved_seats"] == 3 and regular["rule_version"] == "DEMO-v1"
    assert regular["candidate_active_count"] == 3
    assert regular["current_active_count"] is None
    assert regular["remaining_capacity"] == 0 and regular["exceeded"] is False
    assert regular["excess"] == 0
    assert result["findings"] == []

    over = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 4))
    result = assess(client, over, admin)["result"]
    regular = by_category(result)["REGULAR"]
    assert regular["exceeded"] is True and regular["excess"] == 1
    assert regular["remaining_capacity"] == -1
    assert regular["calculation"] == (
        "candidate ACTIVE 4 > approved 3 (rule DEMO-v1, REGULAR) = excess 1"
    )
    finding = result["findings"][0]
    assert finding["rule_id"] == "INTAKE_CATEGORY_EXCEEDED"
    assert finding["severity"] and finding["rule_version"] == "DEMO-v1"
    assert finding["category"] == "REGULAR"


def test_inactive_rows_do_not_count_and_categories_not_pooled(
    client: TestClient, auth_headers: Headers
) -> None:
    admin = auth_headers("cedar_admin")
    spec = [("REGULAR", "ACTIVE")] * 3 + [
        ("NRI", "ACTIVE"),
        ("SUPERNUMERARY", "ACTIVE"),
        ("OCI", "ACTIVE"),
        ("REGULAR", "WITHDRAWN"),
    ]
    batch = upload(client, admin, rows_csv(spec))
    result = assess(client, batch, admin)["result"]
    # 6 ACTIVE overall exceeds the REGULAR cap of 3 if (wrongly) pooled.
    assert result["totals"]["candidate_active_count"] == 6
    assert "not pooled" in result["totals"]["note"]
    assert result["totals"]["candidate_record_count"] == 7
    assert all(not line["exceeded"] for line in result["categories"])
    assert by_category(result)["REGULAR"]["candidate_active_count"] == 3
    assert result["findings"] == []


def test_cap_zero_and_no_rule(client: TestClient, auth_headers: Headers) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    nri = rule_id(client, officer, "NRI")
    assert patch_rule(client, officer, nri, 0).status_code == 200
    none = upload(client, admin, rows_csv([("NRI", "WITHDRAWN")]))
    zero_ok = by_category(assess(client, none, admin)["result"])["NRI"]
    assert zero_ok["approved_seats"] == 0 and zero_ok["exceeded"] is False
    one = upload(client, admin, rows_csv([("NRI", "ACTIVE")]))
    zero_bad = by_category(assess(client, one, admin)["result"])["NRI"]
    assert zero_bad["exceeded"] is True and zero_bad["excess"] == 1
    assert "candidate ACTIVE 1 > approved 0" in zero_bad["calculation"]

    # No DEMO rules are configured for 2027-28: no exceedance claim at all.
    batch = upload(
        client,
        admin,
        rows_csv([("REGULAR", "ACTIVE")] * 5, year="2027-28"),
        year="2027-28",
    )
    result = assess(client, batch, admin)["result"]
    regular = by_category(result)["REGULAR"]
    assert regular["approved_seats"] is None and regular["rule_version"] is None
    assert regular["exceeded"] is False and regular["remaining_capacity"] is None
    assert "no DEMO rule configured" in regular["calculation"]
    assert result["findings"] == []


def test_rule_change_requires_reason_is_audited_and_keeps_history(
    client: TestClient,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    officer, admin = auth_headers("demo_officer"), auth_headers("cedar_admin")
    regular = rule_id(client, officer, "REGULAR")
    for body in (
        {"approved_seats": 2},
        {"approved_seats": 2, "reason": "  "},
        {"approved_seats": 2, "reason": "ab"},
        {"approved_seats": 2, "reason": "x" * 501},
        {"approved_seats": -1, "reason": "valid reason"},
    ):
        response = client.patch(
            f"/api/v1/institutions/{CEDAR}/intake/{regular}",
            headers=officer,
            json=body,
        )
        assert response.status_code == 422, body
    assert patch_rule(client, officer, regular, 3).status_code == 422  # no change

    first = patch_rule(client, officer, regular, 2, "Synthetic first adjustment")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["old_approved_seats"] == 3 and body["new_approved_seats"] == 2
    assert body["old_rule_version"] == body["new_rule_version"] == "DEMO-v1"
    assert body["source_label"] == "DEMO" and "not official" in body["notice"]
    assert (
        patch_rule(client, officer, regular, 5, "Synthetic second").status_code == 200
    )

    history = client.get(
        f"/api/v1/institutions/{CEDAR}/intake/changes", headers=officer
    )
    assert [
        (c["old_approved_seats"], c["new_approved_seats"])
        for c in history.json()["data"]
    ] == [(2, 5), (3, 2)]
    assert history.json()["pagination"]["total"] == 2
    own = client.get(f"/api/v1/institutions/{CEDAR}/intake/changes", headers=admin)
    assert own.status_code == 200 and own.json()["pagination"]["total"] == 2
    paged = client.get(
        f"/api/v1/institutions/{CEDAR}/intake/changes?page_size=1&page=2",
        headers=officer,
    )
    assert len(paged.json()["data"]) == 1
    current = client.get(
        f"/api/v1/institutions/{CEDAR}/intake",
        params={"academic_year": YEAR, "programme_id": str(CEDAR_PROGRAMME)},
        headers=officer,
    ).json()["data"]
    assert next(r for r in current if r["id"] == regular)["approved_seats"] == 5

    events = list(
        seeded_session.scalars(
            select(AuditEvent).where(AuditEvent.action == "INTAKE_RULE_CHANGED")
        )
    )
    assert len(events) == 2
    assert events[0].metadata_redacted["source_label"] == "DEMO"
    assert {e.metadata_redacted["new_approved_seats"] for e in events} == {"2", "5"}
    assert all("reason" not in e.metadata_redacted for e in events)


def test_rule_change_roles_and_scoping(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    regular = rule_id(client, officer, "REGULAR")
    maple_rule = rule_id(client, officer, "REGULAR", "maple")
    for alias in ("cedar_admin", "maple_admin", "demo_manager"):
        assert patch_rule(client, auth_headers(alias), regular, 1).status_code == 403
    assert (
        client.patch(
            f"/api/v1/institutions/{CEDAR}/intake/{regular}",
            json={"approved_seats": 1, "reason": "no auth"},
        ).status_code
        == 401
    )
    # A rule from another institution addressed through this one is not found.
    assert patch_rule(client, officer, maple_rule, 1).status_code == 404
    verifier = seeded_session.scalar(
        select(User).where(User.demo_alias == "demo_manager")
    )
    assert verifier is not None
    verifier.role = Role.AUTHORIZED_VERIFIER
    seeded_session.flush()
    assert (
        patch_rule(client, auth_headers("demo_manager"), regular, 1).status_code == 403
    )
    changes = f"/api/v1/institutions/{CEDAR}/intake/changes"
    assert client.get(changes, headers=auth_headers("demo_manager")).status_code == 403
    assert client.get(changes, headers=auth_headers("maple_admin")).status_code == 404
    assert (
        seeded_session.scalar(select(func.count()).select_from(IntakeRuleChange)) == 0
    )


def test_validation_still_uses_configured_rule_version(
    client: TestClient, auth_headers: Headers
) -> None:
    officer, admin = auth_headers("demo_officer"), auth_headers("cedar_admin")
    regular = rule_id(client, officer, "REGULAR")
    assert patch_rule(client, officer, regular, 2).status_code == 200
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    run_validation(client, batch, admin)
    findings = client.get(
        f"/api/v1/submissions/{batch}/findings?page_size=100", headers=admin
    ).json()["data"]
    exceeded = [f for f in findings if f["rule_code"] == "INTAKE_EXCEEDED"]
    assert exceeded and exceeded[0]["evidence"]["configured_capacity"] == 2
    result = assess(client, batch, admin)["result"]
    assert by_category(result)["REGULAR"]["approved_seats"] == 2


def test_declarations_missing_population_vs_no_reference(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    none = assess(client, batch, admin)["result"]
    assert none["missing_population"] == {"status": "NO_REFERENCE"}
    assert none["snapshot_diff"]["status"] == "NO_CURRENT_SNAPSHOT"
    assert none["findings"] == []

    created = declare(client, admin, 5)
    assert created.status_code == 201, created.text
    assert created.json()["source_label"] == "DEMO"
    result = assess(client, batch, admin)["result"]
    population = result["missing_population"]
    assert population["declared_total"] == 5 and population["shortfall"] == 2
    assert population["candidate_record_count"] == 3 and population["discrepancy"]
    assert "shortfall 2" in population["calculation"]
    assert [f["rule_id"] for f in result["findings"]] == [
        "MISSING_POPULATION_DISCREPANCY"
    ]

    # Latest declaration wins; officers may declare as well.
    assert declare(client, officer, 3).status_code == 201
    latest = client.get(
        f"/api/v1/institutions/{CEDAR}/declarations/latest",
        params={"programme_id": str(CEDAR_PROGRAMME), "academic_year": YEAR},
        headers=admin,
    )
    assert latest.json()["declared_total"] == 3
    again = assess(client, batch, admin)["result"]["missing_population"]
    assert again["shortfall"] == 0 and again["discrepancy"] is False
    listing = client.get(f"/api/v1/institutions/{CEDAR}/declarations", headers=officer)
    assert [d["declared_total"] for d in listing.json()["data"]] == [3, 5]
    assert declare(client, admin, 5).status_code == 201


def test_declaration_validation_and_roles(
    client: TestClient, auth_headers: Headers
) -> None:
    assert declare(client, auth_headers("maple_admin"), 3).status_code == 404
    assert declare(client, auth_headers("demo_manager"), 3).status_code == 403
    admin = auth_headers("cedar_admin")
    assert declare(client, admin, -1).status_code == 422
    unknown = client.post(
        f"/api/v1/institutions/{CEDAR}/declarations",
        headers=admin,
        json={
            "programme_id": str(seed_id("programmes", "maple/DEMO-COMP")),
            "academic_year": YEAR,
            "declared_total": 1,
            "basis": "Synthetic",
        },
    )
    assert unknown.status_code == 404
    latest = f"/api/v1/institutions/{CEDAR}/declarations/latest"
    params = {"programme_id": str(CEDAR_PROGRAMME), "academic_year": YEAR}
    assert client.get(latest, params=params, headers=admin).status_code == 404
    assert (
        client.get(
            f"/api/v1/institutions/{CEDAR}/declarations",
            headers=auth_headers("maple_admin"),
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/institutions/{CEDAR}/declarations",
            headers=auth_headers("demo_manager"),
        ).status_code
        == 403
    )


def activate_initial(client: TestClient, admin: dict[str, str]) -> str:
    initial = upload(
        client, admin, (SAMPLES / "synthetic_snapshot_initial.csv").read_bytes()
    )
    activate_http(client, initial, review(client, initial, admin), admin)
    return initial


def test_removed_records_scenario(client: TestClient, auth_headers: Headers) -> None:
    admin = auth_headers("cedar_admin")
    activate_initial(client, admin)
    replacement = upload(
        client, admin, (SAMPLES / "synthetic_snapshot_replacement.csv").read_bytes()
    )
    first = assess(client, replacement, admin)
    result = first["result"]
    lines = by_category(result)
    assert lines["REGULAR"]["current_active_count"] == 2
    assert lines["NRI"]["current_active_count"] == 1
    assert lines["REGULAR"]["candidate_active_count"] == 0
    assert lines["NRI"]["candidate_active_count"] == 1
    diff = result["snapshot_diff"]
    assert (diff["added_count"], diff["removed_count"], diff["changed_count"]) == (
        0,
        1,
        2,
    )
    assert diff["removed_active_count"] == 1 and diff["changes_total"] == 3
    changes = {c["college_student_id"]: c for c in diff["changes"]}
    assert changes["DEMO-003"]["change_type"] == "REMOVED"
    assert changes["DEMO-001"]["changed_fields"] == ["admission_category"]
    assert set(changes["DEMO-002"]["changed_fields"]) == {
        "student_name",
        "apaar_id",
        "enrollment_status",
        "enrollment_date",
    }
    # No declaration: removed counts only, no conclusion and no findings.
    assert diff["removed_conclusion"] == "NO_REFERENCE"
    assert result["missing_population"] == {"status": "NO_REFERENCE"}
    assert result["findings"] == []
    dump = json.dumps(first)
    assert "Synthetic" not in dump and not re.search(r"\b9\d{11}\b", dump)

    assert declare(client, admin, 3).status_code == 201
    flagged = assess(client, replacement, admin)["result"]
    rules = {f["rule_id"]: f for f in flagged["findings"]}
    assert set(rules) == {
        "MISSING_POPULATION_DISCREPANCY",
        "REMOVED_RECORDS_UNEXPLAINED",
    }
    assert (
        flagged["snapshot_diff"]["removed_conclusion"] == "REMOVED_RECORDS_UNEXPLAINED"
    )
    assert rules["REMOVED_RECORDS_UNEXPLAINED"]["removed_active_count"] == 1
    assert rules["REMOVED_RECORDS_UNEXPLAINED"]["severity"]

    # Declared total equal to the candidate count supports the omission: no flag.
    assert declare(client, admin, 2).status_code == 201
    settled = assess(client, replacement, admin)["result"]
    assert settled["findings"] == []
    assert settled["snapshot_diff"]["removed_conclusion"] == "NO_CONCLUSION"

    listing = client.get(
        f"/api/v1/submissions/{replacement}/intake-assessments", headers=admin
    ).json()
    assert listing["pagination"]["total"] == 3
    assert "result" not in listing["data"][0]
    stored = client.get(
        f"/api/v1/submissions/{replacement}/intake-assessments/{first['id']}",
        headers=admin,
    ).json()
    assert stored["result"] == first["result"]
    assert stored["scope_revision"] == 1 and stored["current_batch_id"]


def test_diff_cap_and_current_batch_assessment(
    client: TestClient, auth_headers: Headers
) -> None:
    admin = auth_headers("cedar_admin")
    initial = activate_initial(client, admin)
    result = assess(client, initial, admin)["result"]
    assert result["is_current_snapshot"] is True
    diff = result["snapshot_diff"]
    assert diff["changes_total"] == 0 and diff["retained_unchanged_count"] == 3
    big = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 250))
    capped = assess(client, big, admin)["result"]["snapshot_diff"]
    assert (
        capped["changes_total"]
        == capped["added_count"] + capped["removed_count"] + capped["changed_count"]
    )
    assert len(capped["changes"]) == 200 and capped["changes_truncated"] is True


def count_rows(session: Session) -> dict[str, Any]:
    return {
        "records": session.scalar(
            select(func.count()).select_from(StudentRecordVersion)
        ),
        "batches": session.scalar(select(func.count()).select_from(SubmissionBatch)),
        "assessments": session.scalar(
            select(func.count()).select_from(IntakeAssessment)
        ),
        "declarations": session.scalar(
            select(func.count()).select_from(IntakeDeclaration)
        ),
        "changes": session.scalar(select(func.count()).select_from(IntakeRuleChange)),
        "revisions": sorted(
            session.execute(
                select(
                    SubmissionScope.id,
                    SubmissionScope.revision,
                    SubmissionScope.current_batch_id,
                )
            ).all()
        ),
    }


def simulate(
    client: TestClient,
    headers: dict[str, str],
    additions: list[dict[str, Any]],
    institution: UUID = CEDAR,
    year: str = YEAR,
) -> Any:
    return client.post(
        f"/api/v1/institutions/{institution}/intake/simulate",
        headers=headers,
        json={
            "programme_id": str(CEDAR_PROGRAMME),
            "academic_year": year,
            "additions": additions,
        },
    )


def test_simulation_is_read_only_and_not_pooled(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin = auth_headers("cedar_admin")
    activate_initial(client, admin)
    before = count_rows(seeded_session)
    simulations = (
        seeded_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "INTAKE_SIMULATED")
        )
        or 0
    )
    response = simulate(
        client,
        admin,
        [
            {"category": "REGULAR", "count": 2},
            {"category": "REGULAR", "count": 0 + 1},
            {"category": "OCI", "count": 1},
        ],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["has_current_snapshot"] is True and body["persisted"] is False
    assert body["source_label"] == "DEMO"
    lines = by_category(body)
    regular = lines["REGULAR"]
    assert (
        regular["before_active_count"],
        regular["added_count"],
        regular["after_active_count"],
    ) == (2, 3, 5)
    assert regular["would_exceed"] is True and regular["excess"] == 2
    assert regular["remaining_capacity"] == -2
    assert regular["calculation"] == (
        "after ACTIVE 5 > approved 3 (rule DEMO-v1, REGULAR) = excess 2"
    )
    assert (
        lines["OCI"]["would_exceed"] is False
        and lines["OCI"]["remaining_capacity"] == 0
    )
    assert (
        lines["NRI"]["before_active_count"] == 1
        and lines["NRI"]["would_exceed"] is False
    )
    assert count_rows(seeded_session) == before
    assert (
        seeded_session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "INTAKE_SIMULATED")
        )
        == simulations + 1
    )


def test_simulation_without_snapshot_validation_and_roles(
    client: TestClient, auth_headers: Headers
) -> None:
    admin = auth_headers("cedar_admin")
    body = simulate(client, admin, [{"category": "NRI", "count": 2}]).json()
    assert body["has_current_snapshot"] is False
    assert by_category(body)["NRI"]["before_active_count"] == 0
    assert by_category(body)["NRI"]["excess"] == 1
    assert (
        simulate(
            client, auth_headers("demo_officer"), [{"category": "NRI", "count": 1}]
        ).status_code
        == 200
    )
    # No rules configured for another year: no exceedance claim.
    empty_year = simulate(
        client, admin, [{"category": "NRI", "count": 9}], year="2027-28"
    )
    nri = by_category(empty_year.json())["NRI"]
    assert nri["approved_seats"] is None and nri["would_exceed"] is False
    for additions in (
        [],
        [{"category": "NRI", "count": 0}],
        [{"category": "BOGUS", "count": 1}],
    ):
        assert simulate(client, admin, additions).status_code == 422
    one = [{"category": "NRI", "count": 1}]
    assert simulate(client, auth_headers("maple_admin"), one).status_code == 404
    assert simulate(client, auth_headers("demo_manager"), one).status_code == 403
    unknown = client.post(
        f"/api/v1/institutions/{CEDAR}/intake/simulate",
        headers=admin,
        json={
            "programme_id": str(seed_id("programmes", "maple/DEMO-COMP")),
            "academic_year": YEAR,
            "additions": one,
        },
    )
    assert unknown.status_code == 404


def test_assessment_role_matrix_and_cross_institution(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin = auth_headers("cedar_admin")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")]))
    created = assess(client, batch, admin)
    url = f"/api/v1/submissions/{batch}/intake-assessments"
    assert client.post(url).status_code == 401
    assert assess(client, batch, auth_headers("demo_officer"))["id"]
    assert assess(client, batch, auth_headers("maple_admin"), 404)
    assert client.get(url, headers=auth_headers("maple_admin")).status_code == 404
    assert (
        client.get(
            f"{url}/{created['id']}", headers=auth_headers("maple_admin")
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{url}/{created['id']}", headers=auth_headers("demo_manager")
        ).status_code
        == 403
    )
    assert assess(client, batch, auth_headers("demo_manager"), 403)
    manager = seeded_session.scalar(
        select(User).where(User.demo_alias == "demo_manager")
    )
    assert manager is not None
    manager.role = Role.AUTHORIZED_VERIFIER
    seeded_session.flush()
    assert assess(client, batch, auth_headers("demo_manager"), 403)
    other = "00000000-0000-4000-8000-000000000000"
    assert client.get(f"{url}/{other}", headers=admin).status_code == 404
    events = list(
        seeded_session.scalars(
            select(AuditEvent).where(AuditEvent.action == "INTAKE_ASSESSMENT_CREATED")
        )
    )
    assert len(events) == 2
    assert "Synthetic" not in json.dumps([e.metadata_redacted for e in events])


def test_history_tables_are_append_only(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    batch = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")]))
    assess(client, batch, admin)
    declare(client, admin, 1)
    patch_rule(client, officer, rule_id(client, officer, "REGULAR"), 1)
    for model, update_values in (
        (IntakeAssessment, {"rule_version": "changed"}),
        (IntakeDeclaration, {"declared_total": 99}),
        (IntakeRuleChange, {"reason": "rewritten history"}),
    ):
        for statement in (update(model).values(**update_values), delete(model)):
            with pytest.raises(DBAPIError), seeded_session.begin_nested():
                seeded_session.execute(statement)
