from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_validation import activate_demo, csv_data, upload

from app.modules.submissions.models import StudentRecordVersion


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
) -> Any:
    return client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "category": category,
            "summary": summary,
            "record_version_ids": record_version_ids,
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
) -> Any:
    body: dict[str, Any] = {"action": action}
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


def test_illegal_transitions_are_rejected(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    officer = auth_headers("demo_officer")
    identifier = upload(client, auth_headers("cedar_admin"))
    ids = record_ids(seeded_session, identifier)
    case_id = open_case(client, officer, ids).json()["id"]

    # Cannot close a case straight from OPEN; must be RESOLVED first.
    assert act(client, case_id, officer, "CLOSED").status_code == 409

    missing_assignee = act(client, case_id, officer, "ASSIGNED")
    assert missing_assignee.status_code == 422

    resolved = act(client, case_id, officer, "RESOLVED")
    assert resolved.status_code == 201
    assert resolved.json()["status"] == "RESOLVED"

    # Closed terminal state accepts no further actions, not even a comment.
    closed = act(client, case_id, officer, "CLOSED")
    assert closed.status_code == 201
    assert closed.json()["status"] == "CLOSED"
    assert act(client, case_id, officer, "COMMENT").status_code == 409


def test_correction_loop_auto_links_new_batch_without_blocking_upload(
    client: TestClient,
    auth_headers: Callable[[str], dict[str, str]],
    seeded_session: Session,
) -> None:
    admin = auth_headers("cedar_admin")
    officer = auth_headers("demo_officer")
    identifier = upload(client, admin, csv_data(apaar_id="900000000002"))
    ids = record_ids(seeded_session, identifier)
    activate_demo(client, identifier, admin)

    case_id = open_case(client, officer, ids, category="APAAR_MISMATCH").json()["id"]
    requested = act(client, case_id, officer, "REQUEST_CORRECTION")
    assert requested.status_code == 201
    assert requested.json()["status"] == "AWAITING_CORRECTION"

    # A corrected reupload is an ordinary upload; it is never blocked by the case.
    corrected = upload(client, admin, csv_data(apaar_id="900000000001"))
    activate_demo(client, corrected, admin)

    refreshed = client.get(f"/api/v1/cases/{case_id}", headers=officer).json()
    assert refreshed["status"] == "UNDER_REVIEW"
    actions = [event["action"] for event in refreshed["events"]]
    assert actions == ["OPENED", "REQUEST_CORRECTION", "CORRECTION_RECEIVED"]
    correction_event = refreshed["events"][-1]
    assert correction_event["linked_batch_id"] == corrected
    assert correction_event["actor_id"] is None

    resolved = act(client, case_id, officer, "RESOLVED")
    assert resolved.status_code == 201
