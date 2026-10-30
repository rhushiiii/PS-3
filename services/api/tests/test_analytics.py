from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from conftest import pin_clock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_intake import (
    assess,
    by_category,
    declare,
    patch_rule,
    rows_csv,
    rule_id,
)
from test_validation import activate_demo, upload

from app.modules.auth.models import User
from app.modules.cases.models import ReviewCase
from app.modules.submissions.models import SubmissionBatch
from app.seed import seed_id

Headers = Callable[[str], dict[str, str]]
YEAR = "2026-27"
BASE = "/api/v1/analytics"
ENDPOINTS = (
    "enrolment-trends",
    "submission-completeness",
    "intake-utilisation",
    "case-performance",
)
CEDAR = seed_id("institutions", "cedar")
MAPLE = seed_id("institutions", "maple")
WILLOW = seed_id("institutions", "willow")
CEDAR_PROGRAMME = seed_id("programmes", "cedar/DEMO-COMP")
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def get(
    client: TestClient, path: str, headers: dict[str, str], **params: Any
) -> dict[str, Any]:
    response = client.get(f"{BASE}/{path}", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return dict(response.json())


def activate(
    client: TestClient,
    headers: dict[str, str],
    spec: list[tuple[str, str]],
    institution: str = "cedar",
) -> str:
    batch = upload(client, headers, rows_csv(spec), institution=institution)
    activate_demo(client, batch, headers)
    return batch


def summary(client: TestClient, headers: dict[str, str], institution: UUID) -> Any:
    response = client.get(
        f"/api/v1/institutions/{institution}/summary",
        params={"academic_year": YEAR},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def programme_row(body: dict[str, Any], programme: UUID) -> dict[str, Any]:
    return next(r for r in body["data"] if r["programme_id"] == str(programme))


# ------------------------------------------------------------------ authorization


@pytest.mark.parametrize("path", ENDPOINTS)
def test_role_matrix(client: TestClient, auth_headers: Headers, path: str) -> None:
    url = f"{BASE}/{path}"
    assert client.get(url).status_code == 401
    for alias in ("cedar_admin", "maple_admin", "demo_verifier"):
        denied = client.get(url, headers=auth_headers(alias))
        assert denied.status_code == 403, alias
        assert denied.json()["error"]["code"] == "FORBIDDEN_ROLE"
    for alias in ("demo_officer", "demo_manager"):
        body = get(client, path, auth_headers(alias))
        assert body["source_label"] == "DEMO" and "as_of" in body
        assert set(body["coverage"]) == {
            "institutions_total",
            "institutions_with_current_snapshot",
            "programmes_total",
            "programmes_with_current_snapshot",
        }
        assert "filters" in body


# ------------------------------------------------------------------ null, not zero


def test_missing_snapshots_are_null_never_zero(
    client: TestClient, auth_headers: Headers
) -> None:
    officer = auth_headers("demo_officer")
    trends = get(
        client, "enrolment-trends", officer, academic_year=YEAR, group_by="institution"
    )
    assert trends["coverage"]["institutions_total"] == 3
    assert trends["coverage"]["institutions_with_current_snapshot"] == 0
    assert trends["coverage"]["programmes_with_current_snapshot"] == 0
    assert len(trends["data"]) == 3
    for row in trends["data"]:
        assert row["status"] == "NO_CURRENT_SNAPSHOT"
        assert row["active_records"] is None and row["declared_records"] is None
        assert row["categories"] is None

    completeness = get(client, "submission-completeness", officer, academic_year=YEAR)
    assert len(completeness["data"]) == 6
    for row in completeness["data"]:
        assert row["has_current_snapshot"] is False
        assert row["freshness_status"] == "NO_CURRENT_SNAPSHOT"
        assert row["freshness_days"] is None and row["stale"] is None
        assert row["last_activated_at"] is None
        assert row["has_declaration"] is False
        assert row["declared_total"] is None and row["shortfall"] is None
        assert row["current_declared_records"] is None

    utilisation = get(client, "intake-utilisation", officer, academic_year=YEAR)
    assert utilisation["data"]
    for row in utilisation["data"]:
        assert row["status"] == "NO_CURRENT_SNAPSHOT"
        assert row["approved_seats"] in (1, 3)
        assert row["current_active"] is None and row["utilisation_pct"] is None
        assert row["remaining_capacity"] is None and row["exceeded"] is None
        assert "unknown (not zero)" in row["calculation"]


def test_year_without_snapshot_is_absent_or_null_not_zero(
    client: TestClient, auth_headers: Headers
) -> None:
    activate(client, auth_headers("cedar_admin"), [("REGULAR", "ACTIVE")])
    officer = auth_headers("demo_officer")
    body = get(client, "enrolment-trends", officer)
    assert [r["academic_year"] for r in body["data"]] == [YEAR]
    other = get(client, "enrolment-trends", officer, academic_year="2027-28")
    row = other["data"][0]
    assert row["status"] == "NO_CURRENT_SNAPSHOT" and row["active_records"] is None


# ------------------------------------------------------------------ reconciliation


def test_totals_reconcile_with_institution_summaries(
    client: TestClient, auth_headers: Headers
) -> None:
    cedar, maple = auth_headers("cedar_admin"), auth_headers("maple_admin")
    activate(
        client,
        cedar,
        [("REGULAR", "ACTIVE")] * 3 + [("NRI", "ACTIVE"), ("OCI", "WITHDRAWN")],
    )
    activate(client, maple, [("REGULAR", "ACTIVE")] * 2 + [("OCI", "ACTIVE")], "maple")
    officer = auth_headers("demo_officer")
    expected = {
        CEDAR: summary(client, cedar, CEDAR)["totals"],
        MAPLE: summary(client, maple, MAPLE)["totals"],
    }
    assert expected[CEDAR]["demo_active_records"] == 4

    overall = get(client, "enrolment-trends", officer, academic_year=YEAR)
    row = overall["data"][0]
    assert row["status"] == "PARTIAL"
    assert row["programmes_total"] == 6 and row["programmes_with_current_snapshot"] == 2
    assert row["active_records"] == sum(
        t["demo_active_records"] for t in expected.values()
    )
    assert row["declared_records"] == sum(
        t["declared_records"] for t in expected.values()
    )
    for category, count in row["categories"].items():
        assert count["active_records"] == sum(
            t["categories"][category]["demo_active_records"] for t in expected.values()
        )
        assert count["declared_records"] == sum(
            t["categories"][category]["declared_records"] for t in expected.values()
        )

    by_institution = get(
        client,
        "enrolment-trends",
        officer,
        academic_year=YEAR,
        group_by="institution",
    )["data"]
    found = {r["institution_id"]: r for r in by_institution}
    for institution, totals in expected.items():
        assert (
            found[str(institution)]["active_records"] == totals["demo_active_records"]
        )
        assert found[str(institution)]["declared_records"] == totals["declared_records"]
    willow = found[str(WILLOW)]
    assert (
        willow["active_records"] is None and willow["status"] == "NO_CURRENT_SNAPSHOT"
    )

    # Filters narrow to the same numbers the summary reports.
    one = get(
        client,
        "enrolment-trends",
        officer,
        academic_year=YEAR,
        institution_id=str(CEDAR),
    )["data"][0]
    assert one["active_records"] == expected[CEDAR]["demo_active_records"]
    regional = get(
        client, "enrolment-trends", officer, academic_year=YEAR, region="DEMO_REGION_2"
    )["data"][0]
    assert regional["active_records"] == expected[MAPLE]["demo_active_records"]
    by_programme = get(
        client,
        "enrolment-trends",
        auth_headers("demo_manager"),
        academic_year=YEAR,
        group_by="programme",
        institution_id=str(CEDAR),
    )["data"]
    assert [r["programme_code"] for r in by_programme] == ["DEMO-COMP", "DEMO-ELEC"]
    comp, elec = by_programme
    assert comp["active_records"] == 4 and elec["active_records"] is None
    assert comp["drilldown"]["programme_id"] == str(CEDAR_PROGRAMME)

    elec_only = get(
        client,
        "enrolment-trends",
        officer,
        academic_year=YEAR,
        programme_code="DEMO-ELEC",
    )
    assert elec_only["coverage"]["programmes_total"] == 3
    assert elec_only["data"][0]["active_records"] is None


# ------------------------------------------------------------------ completeness


def test_staleness_boundary_uses_integrity_threshold(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    batch = activate(client, auth_headers("cedar_admin"), [("REGULAR", "ACTIVE")])
    stamp = seeded_session.scalar(
        select(SubmissionBatch.activated_at).where(SubmissionBatch.id == UUID(batch))
    )
    assert stamp is not None
    officer = auth_headers("demo_officer")
    cases = (
        (timedelta(days=10), 10, False, "FRESH"),
        (timedelta(days=90), 90, False, "FRESH"),  # exactly at the limit
        (timedelta(days=90, minutes=5), 90, True, "STALE"),
        (timedelta(days=200), 200, True, "STALE"),
    )
    for delta, days, stale, status in cases:
        pin_clock(application, stamp + delta)
        body = get(
            client,
            "submission-completeness",
            officer,
            academic_year=YEAR,
            institution_id=str(CEDAR),
        )
        row = programme_row(body, CEDAR_PROGRAMME)
        assert body["stale_after_days"] == 90
        assert body["as_of"].startswith((stamp + delta).strftime("%Y-%m-%dT%H:%M"))
        assert row["freshness_days"] == days and row["stale"] is stale
        assert row["freshness_status"] == status and row["has_current_snapshot"]
        assert datetime.fromisoformat(row["last_activated_at"]) == stamp
    # The other cedar programme has no snapshot: unknown, not stale and not fresh.
    other = [r for r in body["data"] if r["programme_id"] != str(CEDAR_PROGRAMME)][0]
    assert other["stale"] is None and other["freshness_days"] is None

    application.state.settings = application.state.settings.model_copy(
        update={"integrity_stale_days": 150}
    )
    row = programme_row(
        get(client, "submission-completeness", officer, academic_year=YEAR),
        CEDAR_PROGRAMME,
    )
    assert row["stale"] is True  # 200 days > 150
    pin_clock(application, stamp + timedelta(days=150))
    row = programme_row(
        get(client, "submission-completeness", officer, academic_year=YEAR),
        CEDAR_PROGRAMME,
    )
    assert row["stale"] is False


def test_declaration_shortfall_pending_and_region_rollup(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    activate(client, admin, [("REGULAR", "ACTIVE")] * 3)
    before = programme_row(
        get(client, "submission-completeness", officer, academic_year=YEAR),
        CEDAR_PROGRAMME,
    )
    # A current snapshot without a declaration: no shortfall can be computed.
    assert before["has_declaration"] is False and before["shortfall"] is None
    assert before["current_declared_records"] == 3

    assert declare(client, admin, 5).status_code == 201
    upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 2))  # pending candidate
    after = get(client, "submission-completeness", officer, academic_year=YEAR)
    row = programme_row(after, CEDAR_PROGRAMME)
    assert row["declared_total"] == 5 and row["current_declared_records"] == 3
    assert row["shortfall"] == 2 and row["pending_candidate_count"] == 1
    assert row["drilldown"] == {
        "institution_id": str(CEDAR),
        "programme_id": str(CEDAR_PROGRAMME),
        "academic_year": YEAR,
    }

    assert declare(client, admin, 3).status_code == 201  # latest declaration wins
    row = programme_row(
        get(client, "submission-completeness", officer, academic_year=YEAR),
        CEDAR_PROGRAMME,
    )
    assert row["declared_total"] == 3 and row["shortfall"] == 0

    assert declare(client, admin, 9).status_code == 201
    rollups = {
        r["region"]: r
        for r in get(client, "submission-completeness", officer, academic_year=YEAR)[
            "rollups_by_region"
        ]
    }
    cedar = rollups["DEMO_REGION_1"]
    assert cedar["institutions_total"] == 1 and cedar["programme_years_total"] == 2
    assert cedar["with_current_snapshot"] == 1 and cedar["with_declaration"] == 1
    assert cedar["with_shortfall"] == 1 and cedar["pending_candidates"] == 1
    assert rollups["DEMO_REGION_2"]["with_current_snapshot"] == 0

    paged = get(
        client, "submission-completeness", officer, academic_year=YEAR, page_size=2
    )
    assert len(paged["data"]) == 2 and paged["pagination"]["total"] == 6
    assert len(paged["rollups_by_region"]) == 3  # rollups ignore paging


# ------------------------------------------------------------------ utilisation


def test_intake_utilisation_boundary_matches_assessment(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")

    def regular_row(batch: str) -> tuple[dict[str, Any], dict[str, Any]]:
        activate_demo(client, batch, admin)
        rows = get(
            client,
            "intake-utilisation",
            officer,
            academic_year=YEAR,
            institution_id=str(CEDAR),
            programme_code="DEMO-COMP",
        )["data"]
        assert len(rows) == 5  # one per category, never pooled
        line = next(r for r in rows if r["category"] == "REGULAR")
        return line, next(r for r in rows if r["category"] == "NRI")

    equal = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 3))
    calc_equal = by_category(assess(client, equal, admin)["result"])["REGULAR"]
    line, nri = regular_row(equal)
    assert line["status"] == "OK" and line["current_active"] == 3
    assert line["approved_seats"] == 3 and line["rule_version"] == "DEMO-v1"
    assert line["utilisation_pct"] == 100.0 and line["remaining_capacity"] == 0
    assert line["exceeded"] is False and line["excess"] == 0
    assert line["calculation"] in calc_equal["calculation"]
    assert line["remaining_capacity"] == calc_equal["remaining_capacity"]
    # A category with a rule and a snapshot but no ACTIVE rows is a real 0.
    assert nri["current_active"] == 0 and nri["utilisation_pct"] == 0.0
    assert nri["remaining_capacity"] == 1

    over = upload(client, admin, rows_csv([("REGULAR", "ACTIVE")] * 4))
    calc_over = by_category(assess(client, over, admin)["result"])["REGULAR"]
    line, _ = regular_row(over)
    assert line["exceeded"] is True and line["excess"] == 1
    assert line["remaining_capacity"] == -1 and line["utilisation_pct"] == 133.3
    assert line["calculation"] in calc_over["calculation"]
    assert (
        line["calculation"]
        == "ACTIVE 4 > approved 3 (rule DEMO-v1, REGULAR) = excess 1"
    )
    assert line["drilldown"]["programme_id"] == str(CEDAR_PROGRAMME)


def test_utilisation_cap_zero_and_missing_rule(
    client: TestClient, auth_headers: Headers
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    assert (
        patch_rule(client, officer, rule_id(client, officer, "NRI"), 0).status_code
        == 200
    )
    activate(client, admin, [("NRI", "ACTIVE"), ("REGULAR", "ACTIVE")])
    rows = {
        r["category"]: r
        for r in get(
            client,
            "intake-utilisation",
            officer,
            academic_year=YEAR,
            institution_id=str(CEDAR),
            programme_code="DEMO-COMP",
        )["data"]
    }
    nri = rows["NRI"]
    assert nri["approved_seats"] == 0 and nri["utilisation_pct"] is None
    assert nri["exceeded"] is True and nri["excess"] == 1

    none = get(
        client,
        "intake-utilisation",
        officer,
        academic_year="2027-28",
        institution_id=str(CEDAR),
    )
    # No rules and no snapshots: nothing to compare, and no claim either way.
    assert len(none["data"]) == 10
    for row in none["data"]:
        assert row["status"] == "NO_RULE" and row["approved_seats"] is None
        assert row["utilisation_pct"] is None and row["exceeded"] is None
        assert "no DEMO rule configured" in row["calculation"]


# ------------------------------------------------------------------ case performance


def add_case(
    session: Session,
    institution: UUID,
    *,
    opened_at: datetime,
    status: str = "OPEN",
    priority: str = "MEDIUM",
    severity: str = "MEDIUM",
    due_at: datetime | None = None,
    resolved_at: datetime | None = None,
) -> None:
    officer = session.scalar(select(User.id).where(User.demo_alias == "demo_officer"))
    assert officer is not None
    session.add(
        ReviewCase(
            institution_id=institution,
            opened_by=officer,
            category="OTHER",
            summary="Synthetic analytics case",
            status=status,
            priority=priority,
            severity=severity,
            opened_at=opened_at,
            due_at=due_at,
            resolved_at=resolved_at,
        )
    )
    session.flush()


def test_case_ageing_bucket_boundaries(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    pin_clock(application, NOW)
    for age in (0, 7, 8, 14, 15, 30, 31, 90):
        add_case(seeded_session, CEDAR, opened_at=NOW - timedelta(days=age))
    add_case(  # closed cases never age
        seeded_session,
        CEDAR,
        opened_at=NOW - timedelta(days=60),
        status="CLOSED",
        resolved_at=NOW - timedelta(days=50),
    )
    body = get(client, "case-performance", auth_headers("demo_manager"))
    buckets = {b["bucket"]: b for b in body["ageing"]}
    assert {k: v["count"] for k, v in buckets.items()} == {
        "0-7": 2,
        "8-14": 2,
        "15-30": 2,
        "31+": 2,
    }
    assert buckets["8-14"]["drilldown"]["min_age_days"] == "8"
    assert body["totals"]["open"] == 8 and body["totals"]["all"] == 9
    assert sum(b["count"] for b in body["ageing"]) == body["totals"]["open"]


def test_case_overdue_escalated_filters_and_table(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    pin_clock(application, NOW)
    opened = NOW - timedelta(days=20)
    add_case(seeded_session, CEDAR, opened_at=opened, due_at=NOW + timedelta(days=1))
    add_case(seeded_session, CEDAR, opened_at=opened, due_at=NOW - timedelta(days=1))
    add_case(  # exactly 7 days overdue reaches the default escalation threshold
        seeded_session,
        CEDAR,
        opened_at=opened,
        due_at=NOW - timedelta(days=7),
        status="UNDER_REVIEW",
        priority="HIGH",
        severity="HIGH",
    )
    add_case(
        seeded_session,
        MAPLE,
        opened_at=opened,
        due_at=NOW - timedelta(days=30),
        status="RESOLVED",  # closed: not overdue even though past due
        resolved_at=NOW - timedelta(days=5),
    )
    officer = auth_headers("demo_officer")
    body = get(client, "case-performance", officer)
    assert body["totals"] == {"all": 4, "open": 3, "overdue": 2, "escalated": 1}
    status = {s["status"]: s for s in body["by_status"]}
    assert status["OPEN"]["total"] == 2 and status["OPEN"]["overdue"] == 1
    assert status["UNDER_REVIEW"]["escalated"] == 1
    assert status["RESOLVED"]["overdue"] == 0 and status["CLOSED"]["total"] == 0
    assert status["OPEN"]["drilldown"]["status"] == "OPEN"
    table = {r["institution_id"]: r for r in body["data"]}
    assert (table[str(CEDAR)]["open"], table[str(CEDAR)]["overdue"]) == (3, 2)
    assert table[str(MAPLE)]["resolved"] == 1 and table[str(MAPLE)]["open"] == 0
    assert table[str(WILLOW)]["open"] == 0  # true zero: no cases exist
    assert table[str(CEDAR)]["drilldown"]["institution_id"] == str(CEDAR)

    only_high = get(client, "case-performance", officer, priority="HIGH")
    assert (
        only_high["totals"]["all"] == 1 and only_high["filters"]["priority"] == "HIGH"
    )
    assert (
        get(client, "case-performance", officer, severity="HIGH")["totals"]["all"] == 1
    )
    scoped = get(client, "case-performance", officer, institution_id=str(MAPLE))
    assert scoped["totals"]["all"] == 1 and len(scoped["data"]) == 1
    regional = get(client, "case-performance", officer, region="DEMO_REGION_1")
    assert regional["totals"]["all"] == 3
    paged = get(client, "case-performance", officer, page_size=2, page=2)
    assert len(paged["data"]) == 1 and paged["pagination"]["total"] == 3
    assert (
        client.get(
            f"{BASE}/case-performance", headers=officer, params={"priority": "NOPE"}
        ).status_code
        == 422
    )


def test_resolution_time_statistics(
    client: TestClient,
    application: FastAPI,
    auth_headers: Headers,
    seeded_session: Session,
) -> None:
    pin_clock(application, NOW)
    start = NOW - timedelta(days=100)
    for days in (1, 2, 3, 4, 10):
        add_case(
            seeded_session,
            CEDAR,
            opened_at=start,
            status="RESOLVED",
            priority="HIGH",
            resolved_at=start + timedelta(days=days),
        )
    add_case(
        seeded_session,
        MAPLE,
        opened_at=start,
        status="REJECTED",
        priority="LOW",
        resolved_at=start + timedelta(hours=36),
    )
    body = get(client, "case-performance", auth_headers("demo_officer"))
    stats = {s["priority"]: s for s in body["resolution_days"]}
    assert stats["HIGH"] == {
        "priority": "HIGH",
        "resolved_count": 5,
        "mean_days": 4.0,
        "median_days": 3.0,
        "p90_days": 10.0,  # nearest rank: ceil(0.9 * 5) = 5th value
    }
    assert stats["LOW"]["resolved_count"] == 1 and stats["LOW"]["median_days"] == 1.5
    assert stats["URGENT"] == {
        "priority": "URGENT",
        "resolved_count": 0,
        "mean_days": None,
        "median_days": None,
        "p90_days": None,
    }
    assert stats["ALL"]["resolved_count"] == 6
    assert stats["ALL"]["mean_days"] == round((20 + 1.5) / 6, 2)


# ------------------------------------------------------------------ privacy


def test_no_apaar_names_or_student_ids_in_any_response(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    admin, officer = auth_headers("cedar_admin"), auth_headers("demo_officer")
    activate(client, admin, [("REGULAR", "ACTIVE")] * 4 + [("NRI", "ACTIVE")])
    add_case(seeded_session, CEDAR, opened_at=datetime.now(UTC))
    for path in ENDPOINTS:
        text = client.get(f"{BASE}/{path}", headers=officer).text
        lowered = text.lower()
        for forbidden in ("9000000", "DEMO-I00", "Synthetic 1", "apaar", "full_name"):
            assert forbidden.lower() not in lowered, (path, forbidden)
        assert "@" not in text
