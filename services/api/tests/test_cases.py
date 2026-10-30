from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from test_validation import activate_demo, csv_data, upload

from app.modules.audit.models import AuditEvent
from app.modules.auth.models import Role, User
from app.modules.cases.models import CaseRecord
from app.modules.submissions.models import StudentRecordVersion
from app.seed import seed_id


def record_ids(session: Session, batch_id: str) -> list[str]:
    return [
        str(row.id)
        for row in session.scalars(
            select(StudentRecordVersion).where(
                StudentRecordVersion.batch_id == batch_id
            )
        )
    ]


def open_case(
    client: TestClient,
    headers: dict[str, str],
    record_version_ids: list[str],
    *,
    category: str = "POTENTIAL_DUPLICATE",
    summary: str = "Two institutions report overlapping APAAR values",
    **extra: Any,
) -> Any:
    return client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "category": category,
            "summary": summary,
            "record_version_ids": record_version_ids,
            **extra,
        },
    )


def act(
    client: TestClient,
    case_id: str,
    headers: dict[str, str],
    action: str,
    *,
    comment: str | None = None,
    assigned_to: str | None = None,
    **extra: Any,
) -> Any:
    body: dict[str, Any] = {"action": action, **extra}
    if comment is not None:
        body["comment"] = comment
    if assigned_to is not None:
        body["assigned_to"] = assigned_to
    return client.post(f"/api/v1/cases/{case_id}/actions", headers=headers, json=body)


def test_officer_opens_case_and_institution_admin_cannot(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    identifier = upload(client, admin)
    ids = record_ids(seeded_session, identifier)

    denied = open_case(client, admin, ids)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN_ROLE"

    opened = open_case(client, officer, ids)
    assert opened.status_code == 201, opened.text
    body = opened.json()
    assert body["status"] == "OPEN"
    assert sorted(body["record_version_ids"]) == sorted(ids)
    assert [event["action"] for event in body["events"]] == ["OPENED"]


def test_manager_cannot_open_list_or_act_on_cases(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    manager = auth_headers("demo_manager")
    identifier = upload(client, admin)
    ids = record_ids(seeded_session, identifier)
    case_id = open_case(client, officer, ids).json()["id"]

    assert open_case(client, manager, ids).status_code == 403
    assert client.get("/api/v1/cases", headers=manager).status_code == 403
    assert client.get(f"/api/v1/cases/{case_id}", headers=manager).status_code == 403
    assert act(client, case_id, manager, "COMMENT").status_code == 403


def test_case_cannot_span_multiple_institutions(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    officer = auth_headers("demo_officer")
    cedar_batch = upload(client, auth_headers("cedar_admin"))
    maple_batch = upload(client, auth_headers("maple_admin"), institution="maple")
    mixed = record_ids(seeded_session, cedar_batch) + record_ids(
        seeded_session, maple_batch
    )
    response = open_case(client, officer, mixed)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_unknown_record_version_id_is_not_found(
    client: TestClient, auth_headers: Callable[[str], dict[str, str]]
) -> None:
    response = open_case(
        client,
        auth_headers("demo_officer"),
        ["00000000-0000-0000-0000-000000000000"],
    )
    assert response.status_code == 404


def test_institution_admin_reads_own_case_but_not_other_institutions(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    cedar_admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    identifier = upload(client, cedar_admin)
    ids = record_ids(seeded_session, identifier)
    case_id = open_case(client, officer, ids).json()["id"]

    own = client.get(f"/api/v1/cases/{case_id}", headers=cedar_admin)
    assert own.status_code == 200

    own_list = client.get("/api/v1/cases", headers=cedar_admin)
    assert own_list.status_code == 200
    assert own_list.json()["pagination"]["total"] == 1

    other = auth_headers("maple_admin")
    assert client.get(f"/api/v1/cases/{case_id}", headers=other).status_code == 404


def test_institution_admin_may_only_comment(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    cedar_admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    identifier = upload(client, cedar_admin)
    ids = record_ids(seeded_session, identifier)
    case_id = open_case(client, officer, ids).json()["id"]

    denied = act(client, case_id, cedar_admin, "REQUEST_CORRECTION")
    assert denied.status_code == 403

    allowed = act(client, case_id, cedar_admin, "COMMENT", comment="Investigating")
    assert allowed.status_code == 201


def officer_id(session: Session) -> str:
    return str(seed_id("users", "demo_officer"))


def add_officer(session: Session, alias: str, *, active: bool = True) -> User:
    user = User(
        email=f"{alias}@sih26263.invalid",
        role=Role.AICTE_OFFICER,
        institution_id=None,
        active=active,
        demo_alias=alias,
        is_demo=True,
    )
    session.add(user)
    session.flush()
    return user


REASON = {"resolution_reason": "Reviewed against synthetic evidence"}
ALL_ACTIONS = (
    "COMMENT",
    "ASSIGNED",
    "START_REVIEW",
    "REQUEST_CORRECTION",
    "UPDATED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
)
# Independent statement of the lifecycle (officer-initiated actions).
ALLOWED = {
    "OPEN": {"COMMENT", "ASSIGNED", "START_REVIEW", "REQUEST_CORRECTION", "UPDATED"},
    "ASSIGNED": {
        "COMMENT",
        "ASSIGNED",
        "START_REVIEW",
        "REQUEST_CORRECTION",
        "UPDATED",
    },
    "UNDER_REVIEW": {
        "COMMENT",
        "ASSIGNED",
        "REQUEST_CORRECTION",
        "RESOLVED",
        "REJECTED",
        "UPDATED",
    },
    "AWAITING_CORRECTION": {"COMMENT", "ASSIGNED", "UPDATED"},
    "RESPONSE_SUBMITTED": {
        "COMMENT",
        "ASSIGNED",
        "START_REVIEW",
        "REQUEST_CORRECTION",
        "UPDATED",
    },
    "RESOLVED": {"COMMENT", "CLOSED"},
    "REJECTED": {"COMMENT", "CLOSED"},
    "CLOSED": set(),
}
RESULT_STATUS = {
    "START_REVIEW": "UNDER_REVIEW",
    "REQUEST_CORRECTION": "AWAITING_CORRECTION",
    "RESOLVED": "RESOLVED",
    "REJECTED": "REJECTED",
    "CLOSED": "CLOSED",
}
PATHS: dict[str, list[tuple[str, str]]] = {
    "OPEN": [],
    "ASSIGNED": [("officer", "ASSIGNED")],
    "UNDER_REVIEW": [("officer", "START_REVIEW")],
    "AWAITING_CORRECTION": [("officer", "REQUEST_CORRECTION")],
    "RESPONSE_SUBMITTED": [
        ("officer", "REQUEST_CORRECTION"),
        ("admin", "RESPONSE_SUBMITTED"),
    ],
    "RESOLVED": [("officer", "START_REVIEW"), ("officer", "RESOLVED")],
    "REJECTED": [("officer", "START_REVIEW"), ("officer", "REJECTED")],
    "CLOSED": [
        ("officer", "START_REVIEW"),
        ("officer", "RESOLVED"),
        ("officer", "CLOSED"),
    ],
}


def action_body(action: str, assignee: str) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if action == "ASSIGNED":
        body["assigned_to"] = assignee
    if action in {"RESOLVED", "REJECTED"}:
        body.update(REASON)
    if action == "UPDATED":
        body["priority"] = "HIGH"
    return body


def case_in_status(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    assignee: str,
    status: str,
) -> str:
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    for who, action in PATHS[status]:
        response = act(
            client, case_id, heads[who], action, **action_body(action, assignee)
        )
        assert response.status_code == 201, response.text
    return str(case_id)


@pytest.fixture
def heads(
    auth_headers: Callable[[str], dict[str, str]],
) -> dict[str, dict[str, str]]:
    return {
        "admin": auth_headers("cedar_admin"),
        "other_admin": auth_headers("maple_admin"),
        "officer": auth_headers("demo_officer"),
        "manager": auth_headers("demo_manager"),
    }


@pytest.fixture
def ids(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    seeded_session: Session,
) -> list[str]:
    return record_ids(seeded_session, upload(client, heads["admin"]))


@pytest.mark.parametrize("status", list(ALLOWED))
def test_transition_table(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
    status: str,
) -> None:
    assignee = officer_id(seeded_session)
    for action in ALL_ACTIONS:
        case_id = case_in_status(client, heads, ids, assignee, status)
        before = client.get(f"/api/v1/cases/{case_id}", headers=heads["officer"])
        assert before.json()["status"] == status
        response = act(
            client,
            case_id,
            heads["officer"],
            action,
            **action_body(action, assignee),
        )
        if action in ALLOWED[status]:
            assert response.status_code == 201, (status, action, response.text)
            body = response.json()
            expected = RESULT_STATUS.get(action, status)
            if action == "ASSIGNED" and status in {"OPEN", "ASSIGNED"}:
                expected = "ASSIGNED"
            assert body["status"] == expected, (status, action)
            last = body["events"][-1]
            assert last["action"] == action
            assert last["actor_id"] == assignee
            assert last["created_at"]
        else:
            assert response.status_code == 409, (status, action, response.text)
            assert response.json()["error"]["code"] == "INVALID_CASE_TRANSITION"


def test_officer_cannot_submit_response_and_admin_only_when_awaiting(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    assignee = officer_id(seeded_session)
    for status in ALLOWED:
        case_id = case_in_status(client, heads, ids, assignee, status)
        assert (
            act(client, case_id, heads["officer"], "RESPONSE_SUBMITTED").status_code
            == 403
        )
        assert (
            act(client, case_id, heads["manager"], "RESPONSE_SUBMITTED").status_code
            == 403
        )
        assert (
            act(client, case_id, heads["other_admin"], "RESPONSE_SUBMITTED").status_code
            == 404
        )
        response = act(client, case_id, heads["admin"], "RESPONSE_SUBMITTED")
        if status == "AWAITING_CORRECTION":
            assert response.status_code == 201
            assert response.json()["status"] == "RESPONSE_SUBMITTED"
            assert response.json()["events"][-1]["actor_id"] != assignee
        else:
            assert response.status_code == 409


def test_admin_cannot_use_officer_actions(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    assignee = officer_id(seeded_session)
    case_id = case_in_status(client, heads, ids, assignee, "UNDER_REVIEW")
    for action in ("ASSIGNED", "START_REVIEW", "UPDATED", "RESOLVED", "REJECTED"):
        response = act(
            client, case_id, heads["admin"], action, **action_body(action, assignee)
        )
        assert response.status_code == 403, action


def test_resolution_reason_required_and_evidence_untouched(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    assignee = officer_id(seeded_session)

    def snapshot() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        links = seeded_session.scalars(select(CaseRecord))
        versions = seeded_session.scalars(select(StudentRecordVersion))
        return (
            sorted((str(r.id), str(r.record_version_id)) for r in links),
            sorted((str(r.id), str(r.original_json)) for r in versions),
        )

    for action in ("RESOLVED", "REJECTED"):
        case_id = case_in_status(client, heads, ids, assignee, "UNDER_REVIEW")
        evidence = snapshot()
        assert act(client, case_id, heads["officer"], action).status_code == 422
        blank = act(client, case_id, heads["officer"], action, resolution_reason="  ")
        assert blank.status_code == 422
        too_long = act(
            client, case_id, heads["officer"], action, resolution_reason="x" * 2001
        )
        assert too_long.status_code == 422
        done = act(
            client,
            case_id,
            heads["officer"],
            action,
            comment="Closing out",
            resolution_reason=" Verified  with institution ",
        )
        assert done.status_code == 201
        body = done.json()
        assert body["status"] == action
        assert body["resolution_reason"] == "Verified  with institution"
        assert body["resolved_at"] is not None
        assert snapshot() == evidence
    stray = open_case(client, heads["officer"], ids).json()["id"]
    assert (
        act(
            client, stray, heads["officer"], "COMMENT", resolution_reason="nope"
        ).status_code
        == 422
    )


def test_assignment_validation_and_reassignment(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    second = add_officer(seeded_session, "second_officer")
    inactive = add_officer(seeded_session, "inactive_officer", active=False)
    admin_user = seeded_session.scalar(
        select(User).where(User.demo_alias == "cedar_admin")
    )
    manager_user = seeded_session.scalar(
        select(User).where(User.demo_alias == "demo_manager")
    )
    assert admin_user is not None and manager_user is not None
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    for bad in (
        admin_user.id,
        manager_user.id,
        inactive.id,
        "00000000-0000-0000-0000-000000000000",
    ):
        response = act(
            client, case_id, heads["officer"], "ASSIGNED", assigned_to=str(bad)
        )
        assert response.status_code == 422, bad
    assert act(client, case_id, heads["officer"], "ASSIGNED").status_code == 422

    first = act(
        client,
        case_id,
        heads["officer"],
        "ASSIGNED",
        assigned_to=officer_id(seeded_session),
    )
    assert first.json()["status"] == "ASSIGNED"
    again = act(
        client, case_id, heads["officer"], "ASSIGNED", assigned_to=str(second.id)
    )
    assert again.status_code == 201
    assert again.json()["assigned_to"] == str(second.id)
    assert again.json()["status"] == "ASSIGNED"

    act(client, case_id, heads["officer"], "START_REVIEW")
    moved = act(
        client,
        case_id,
        heads["officer"],
        "ASSIGNED",
        assigned_to=officer_id(seeded_session),
    )
    assert moved.json()["status"] == "UNDER_REVIEW"
    assert moved.json()["assigned_to"] == officer_id(seeded_session)


def test_assignees_endpoint_is_officer_only_and_hides_email(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    seeded_session: Session,
) -> None:
    add_officer(seeded_session, "second_officer")
    add_officer(seeded_session, "inactive_officer", active=False)
    for who in ("admin", "manager"):
        assert (
            client.get("/api/v1/cases/assignees", headers=heads[who]).status_code == 403
        )
    assert client.get("/api/v1/cases/assignees").status_code == 401
    response = client.get("/api/v1/cases/assignees", headers=heads["officer"])
    assert response.status_code == 200
    names = {row["display_name"] for row in response.json()}
    # demo_officer_2 is a seeded active officer (added with the verifier phase).
    assert names == {"demo_officer", "demo_officer_2", "second_officer"}
    assert all(set(row) == {"id", "display_name"} for row in response.json())
    assert "sih26263.invalid" not in response.text


def test_due_date_defaults_and_overrides(
    client: TestClient, heads: dict[str, dict[str, str]], ids: list[str]
) -> None:
    defaults = {"LOW": 30, "MEDIUM": 14, "HIGH": 7, "URGENT": 3}
    for priority, days in defaults.items():
        body = open_case(client, heads["officer"], ids, priority=priority).json()
        assert body["priority"] == priority
        due = datetime.fromisoformat(body["due_at"])
        opened = datetime.fromisoformat(body["opened_at"])
        assert due - opened == timedelta(days=days)
    plain = open_case(client, heads["officer"], ids).json()
    assert (plain["priority"], plain["severity"]) == ("MEDIUM", "MEDIUM")
    explicit = datetime(2030, 1, 1, tzinfo=UTC)
    custom = open_case(
        client,
        heads["officer"],
        ids,
        severity="CRITICAL",
        due_at=explicit.isoformat(),
    ).json()
    assert datetime.fromisoformat(custom["due_at"]) == explicit
    assert custom["severity"] == "CRITICAL"
    for bad in (
        {"priority": "EXTREME"},
        {"severity": "EXTREME"},
        {"due_at": "2030-01-01T00:00:00"},
    ):
        assert open_case(client, heads["officer"], ids, **bad).status_code == 422


def test_overdue_and_escalation_flags(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    now = datetime.now(UTC)

    def flags(offset: timedelta) -> dict[str, Any]:
        body = open_case(
            client, heads["officer"], ids, due_at=(now + offset).isoformat()
        ).json()
        return dict(body)

    future = flags(timedelta(days=1))
    assert (future["is_overdue"], future["is_escalated"]) == (False, False)
    late = flags(-timedelta(days=1))
    assert (late["is_overdue"], late["is_escalated"]) == (True, False)
    very_late = flags(-timedelta(days=8))
    assert (very_late["is_overdue"], very_late["is_escalated"]) == (True, True)
    assert very_late["age_days"] == 0

    # Finished cases are never overdue.
    case_id = very_late["id"]
    act(client, case_id, heads["officer"], "START_REVIEW")
    done = act(client, case_id, heads["officer"], "REJECTED", **REASON)
    assert (done.json()["is_overdue"], done.json()["is_escalated"]) == (False, False)

    # Priority/due date changes are recorded as UPDATED events without PII.
    moved = act(
        client,
        late["id"],
        heads["officer"],
        "UPDATED",
        priority="URGENT",
        due_at=(now + timedelta(days=5)).isoformat(),
    )
    assert moved.status_code == 201
    assert moved.json()["priority"] == "URGENT"
    assert moved.json()["is_overdue"] is False
    event = moved.json()["events"][-1]
    assert event["action"] == "UPDATED"
    assert "priority: MEDIUM -> URGENT" in event["comment"]
    assert "due_at" in event["comment"]

    assert act(client, late["id"], heads["officer"], "UPDATED").status_code == 422
    unchanged = act(client, late["id"], heads["officer"], "UPDATED", priority="URGENT")
    assert unchanged.status_code == 422
    assert (
        act(client, case_id, heads["officer"], "UPDATED", severity="LOW").status_code
        == 409
    )


def test_list_filters_and_institution_isolation(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    seeded_session: Session,
) -> None:
    officer = heads["officer"]
    cedar = record_ids(seeded_session, upload(client, heads["admin"]))
    maple = record_ids(
        seeded_session,
        upload(client, heads["other_admin"], institution="maple"),
    )
    now = datetime.now(UTC)
    first = open_case(
        client,
        officer,
        cedar,
        priority="HIGH",
        severity="CRITICAL",
        due_at=(now - timedelta(days=2)).isoformat(),
    ).json()["id"]
    second = open_case(client, officer, cedar, priority="LOW", severity="LOW").json()[
        "id"
    ]
    third = open_case(client, officer, maple, priority="HIGH", severity="LOW").json()[
        "id"
    ]
    act(client, second, officer, "START_REVIEW")
    act(client, first, officer, "ASSIGNED", assigned_to=officer_id(seeded_session))

    def found(headers: dict[str, str], **params: Any) -> set[str]:
        response = client.get("/api/v1/cases", headers=headers, params=params)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["pagination"]["total"] == len(data["data"])
        return {row["id"] for row in data["data"]}

    assert found(officer) == {first, second, third}
    assert found(officer, institution_id=str(seed_id("institutions", "maple"))) == {
        third
    }
    assert found(officer, status="ASSIGNED") == {first}
    assert found(officer, status="UNDER_REVIEW") == {second}
    assert found(officer, severity="LOW") == {second, third}
    assert found(officer, priority="HIGH") == {first, third}
    assert found(officer, assigned_to=officer_id(seeded_session)) == {first}
    assert found(officer, overdue="true") == {first}
    assert found(officer, overdue="false") == {second, third}
    assert found(officer, min_age_days=1) == set()
    assert found(officer, min_age_days=0) == {first, second, third}
    assert found(
        officer, programme_id=str(seed_id("programmes", "cedar/DEMO-COMP"))
    ) == {first, second}
    assert found(
        officer, programme_id=str(seed_id("programmes", "maple/DEMO-COMP"))
    ) == {third}
    assert (
        found(officer, programme_id=str(seed_id("programmes", "cedar/DEMO-ELEC")))
        == set()
    )
    assert found(officer, priority="HIGH", severity="LOW", overdue="false") == {third}

    # Institution admins stay inside their own institution whatever they ask for.
    assert found(heads["admin"]) == {first, second}
    assert found(heads["admin"], priority="HIGH") == {first}
    assert (
        found(heads["admin"], institution_id=str(seed_id("institutions", "maple")))
        == set()
    )
    assert found(heads["other_admin"]) == {third}
    assert (
        found(
            heads["other_admin"], institution_id=str(seed_id("institutions", "cedar"))
        )
        == set()
    )

    # Invalid filter values are rejected, and managers stay locked out.
    for params in (
        {"status": "BOGUS"},
        {"priority": "BOGUS"},
        {"severity": "BOGUS"},
        {"overdue": "maybe"},
        {"min_age_days": -1},
        {"institution_id": "not-a-uuid"},
    ):
        response = client.get("/api/v1/cases", headers=officer, params=params)
        assert response.status_code == 422, params
    assert (
        client.get(
            "/api/v1/cases", headers=heads["manager"], params={"priority": "HIGH"}
        ).status_code
        == 403
    )


def test_min_age_days_uses_opened_at(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    seeded_session.execute(
        text("UPDATE review_cases SET opened_at = now() - interval '10 days'")
    )
    listed = client.get(
        "/api/v1/cases", headers=heads["officer"], params={"min_age_days": 10}
    ).json()
    assert [row["id"] for row in listed["data"]] == [case_id]
    assert listed["data"][0]["age_days"] == 10
    assert (
        client.get(
            "/api/v1/cases", headers=heads["officer"], params={"min_age_days": 11}
        ).json()["pagination"]["total"]
        == 0
    )


def test_full_workflow_loop_with_audit_and_notifications(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    seeded_session: Session,
) -> None:
    admin, officer = heads["admin"], heads["officer"]
    assignee = officer_id(seeded_session)
    identifier = upload(client, admin, csv_data(apaar_id="900000000002"))
    ids = record_ids(seeded_session, identifier)
    activate_demo(client, identifier, admin)
    evidence = client.get("/api/v1/cases", headers=officer).json()["pagination"][
        "total"
    ]
    assert evidence == 0

    case_id = open_case(
        client, officer, ids, category="APAAR_MISMATCH", priority="URGENT"
    ).json()["id"]
    assert (
        act(client, case_id, officer, "ASSIGNED", assigned_to=assignee).status_code
        == 201
    )
    requested = act(client, case_id, officer, "REQUEST_CORRECTION", comment="Fix it")
    assert requested.json()["status"] == "AWAITING_CORRECTION"

    # A corrected reupload is ordinary and never blocked; it answers the case.
    corrected = upload(client, admin, csv_data(apaar_id="900000000001"))
    activate_demo(client, corrected, admin)
    answered = client.get(f"/api/v1/cases/{case_id}", headers=officer).json()
    assert answered["status"] == "RESPONSE_SUBMITTED"
    auto = answered["events"][-1]
    assert auto["action"] == "CORRECTION_RECEIVED"
    assert auto["linked_batch_id"] == corrected
    assert auto["actor_id"] is None

    assert (
        act(client, case_id, officer, "START_REVIEW").json()["status"] == "UNDER_REVIEW"
    )
    resolved = act(client, case_id, officer, "RESOLVED", **REASON)
    assert resolved.json()["status"] == "RESOLVED"
    closed = act(client, case_id, officer, "CLOSED")
    assert closed.json()["status"] == "CLOSED"
    assert act(client, case_id, officer, "COMMENT").status_code == 409

    final = client.get(f"/api/v1/cases/{case_id}", headers=admin).json()
    assert [event["action"] for event in final["events"]] == [
        "OPENED",
        "ASSIGNED",
        "REQUEST_CORRECTION",
        "CORRECTION_RECEIVED",
        "START_REVIEW",
        "RESOLVED",
        "CLOSED",
    ]
    assert final["record_version_ids"] == ids
    audit = {
        row.action
        for row in seeded_session.scalars(
            select(AuditEvent).where(AuditEvent.entity_id == UUID(case_id))
        )
    }
    assert audit == {
        "CASE_OPENED",
        "CASE_ASSIGNED",
        "CASE_REQUEST_CORRECTION",
        "CASE_START_REVIEW",
        "CASE_RESOLVED",
        "CASE_CLOSED",
    }
