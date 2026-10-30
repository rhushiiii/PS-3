from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_cases import REASON, act, add_officer, officer_id, open_case, record_ids
from test_validation import activate_demo, csv_data, upload

from app.modules.auth.models import Role, User
from app.modules.notifications.models import Notification
from app.modules.notifications.services import ensure_overdue_notifications
from app.seed import seed_id


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


def user_id(session: Session, alias: str) -> Any:
    return seed_id("users", alias)


def rows(session: Session, **filters: Any) -> list[Notification]:
    statement = select(Notification).order_by(Notification.created_at, Notification.id)
    for name, value in filters.items():
        statement = statement.where(getattr(Notification, name) == value)
    return list(session.scalars(statement))


def inbox(
    client: TestClient, headers: dict[str, str], **params: Any
) -> list[dict[str, Any]]:
    response = client.get("/api/v1/notifications", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return list(response.json()["data"])


def test_assignment_notifies_only_the_assignee(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    second = add_officer(seeded_session, "second_officer")
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    act(client, case_id, heads["officer"], "ASSIGNED", assigned_to=str(second.id))

    created = rows(seeded_session, case_id=case_id)
    assert [(n.kind, n.recipient_user_id) for n in created] == [
        ("CASE_ASSIGNED", second.id)
    ]
    assert inbox(client, heads["officer"]) == []
    assert inbox(client, heads["admin"]) == []
    note = created[0]
    assert str(case_id)[:8] in note.title
    assert "Demo Cedar Institute" in note.body
    text = (note.title + note.body).lower()
    for private in ("synthetic one", "demo-one", "900000000001"):
        assert private not in text


def test_correction_request_goes_to_active_institution_admins_only(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    cedar = seed_id("institutions", "cedar")
    extra = User(
        email="cedar_two@sih26263.invalid",
        role=Role.INSTITUTION_ADMIN,
        institution_id=cedar,
        active=True,
        demo_alias="cedar_two",
        is_demo=True,
    )
    inactive = User(
        email="cedar_gone@sih26263.invalid",
        role=Role.INSTITUTION_ADMIN,
        institution_id=cedar,
        active=False,
        demo_alias="cedar_gone",
        is_demo=True,
    )
    seeded_session.add_all([extra, inactive])
    seeded_session.flush()
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    act(client, case_id, heads["officer"], "REQUEST_CORRECTION")

    recipients = {
        n.recipient_user_id for n in rows(seeded_session, kind="CORRECTION_REQUESTED")
    }
    assert recipients == {user_id(seeded_session, "cedar_admin"), extra.id}
    assert [n["kind"] for n in inbox(client, heads["admin"])] == [
        "CORRECTION_REQUESTED"
    ]
    assert inbox(client, heads["other_admin"]) == []
    assert inbox(client, heads["officer"]) == []


def test_response_goes_to_assignee_else_all_active_officers(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    second = add_officer(seeded_session, "second_officer")
    add_officer(seeded_session, "inactive_officer", active=False)
    first = user_id(seeded_session, "demo_officer")
    # demo_officer_2 is seeded and active, so it is also a fallback recipient.
    seeded_second = user_id(seeded_session, "demo_officer_2")

    assigned = open_case(client, heads["officer"], ids).json()["id"]
    act(client, assigned, heads["officer"], "ASSIGNED", assigned_to=str(second.id))
    act(client, assigned, heads["officer"], "REQUEST_CORRECTION")
    act(client, assigned, heads["admin"], "RESPONSE_SUBMITTED")
    got = rows(seeded_session, case_id=assigned, kind="RESPONSE_SUBMITTED")
    assert [n.recipient_user_id for n in got] == [second.id]

    unassigned = open_case(client, heads["officer"], ids).json()["id"]
    act(client, unassigned, heads["officer"], "REQUEST_CORRECTION")
    act(client, unassigned, heads["admin"], "RESPONSE_SUBMITTED")
    got = rows(seeded_session, case_id=unassigned, kind="RESPONSE_SUBMITTED")
    assert {n.recipient_user_id for n in got} == {first, seeded_second, second.id}


def test_automatic_correction_received_notifies_in_activation_transaction(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    seeded_session: Session,
) -> None:
    admin, officer = heads["admin"], heads["officer"]
    identifier = upload(client, admin, csv_data(apaar_id="900000000002"))
    ids = record_ids(seeded_session, identifier)
    activate_demo(client, identifier, admin)
    case_id = open_case(client, officer, ids).json()["id"]
    act(client, case_id, officer, "ASSIGNED", assigned_to=officer_id(seeded_session))
    act(client, case_id, officer, "REQUEST_CORRECTION")
    assert rows(seeded_session, kind="RESPONSE_SUBMITTED") == []

    corrected = upload(client, admin, csv_data(apaar_id="900000000001"))
    activate_demo(client, corrected, admin)
    got = rows(seeded_session, kind="RESPONSE_SUBMITTED")
    assert [n.recipient_user_id for n in got] == [
        user_id(seeded_session, "demo_officer")
    ]
    assert str(got[0].case_id) == case_id
    assert "900000000001" not in got[0].body + got[0].title


@pytest.mark.parametrize(
    ("action", "kind"),
    [
        ("RESOLVED", "CASE_RESOLVED"),
        ("REJECTED", "CASE_REJECTED"),
        ("CLOSED", "CASE_CLOSED"),
    ],
)
def test_outcomes_notify_institution_admins(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
    action: str,
    kind: str,
) -> None:
    officer = heads["officer"]
    case_id = open_case(client, officer, ids).json()["id"]
    act(client, case_id, officer, "START_REVIEW")
    if action == "CLOSED":
        act(client, case_id, officer, "RESOLVED", **REASON)
    act(client, case_id, officer, action, **(REASON if action != "CLOSED" else {}))
    got = rows(seeded_session, case_id=case_id, kind=kind)
    assert [n.recipient_user_id for n in got] == [
        user_id(seeded_session, "cedar_admin")
    ]
    assert inbox(client, heads["other_admin"]) == []
    assert kind in {n["kind"] for n in inbox(client, heads["admin"])}


def test_unread_count_mark_read_and_read_all(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
) -> None:
    admin, officer = heads["admin"], heads["officer"]
    for _ in range(3):
        case_id = open_case(client, officer, ids).json()["id"]
        act(client, case_id, officer, "REQUEST_CORRECTION")

    count = client.get("/api/v1/notifications/unread-count", headers=admin)
    assert count.json() == {"unread": 3}
    assert client.get("/api/v1/notifications/unread-count", headers=officer).json() == {
        "unread": 0
    }
    first_page = client.get(
        "/api/v1/notifications", headers=admin, params={"page_size": 2}
    ).json()
    assert first_page["pagination"] == {"page": 1, "page_size": 2, "total": 3}
    assert len(first_page["data"]) == 2

    target = first_page["data"][0]["id"]
    marked = client.post(f"/api/v1/notifications/{target}/read", headers=admin)
    assert marked.status_code == 200
    read_at = marked.json()["read_at"]
    assert read_at is not None
    again = client.post(f"/api/v1/notifications/{target}/read", headers=admin)
    assert again.json()["read_at"] == read_at
    assert client.get("/api/v1/notifications/unread-count", headers=admin).json() == {
        "unread": 2
    }
    assert len(inbox(client, admin, unread="true")) == 2
    assert len(inbox(client, admin)) == 3

    everything = client.post("/api/v1/notifications/read-all", headers=admin)
    assert everything.json() == {"marked_read": 2}
    assert inbox(client, admin, unread="true") == []
    assert client.post("/api/v1/notifications/read-all", headers=admin).json() == {
        "marked_read": 0
    }


def test_users_only_touch_their_own_notifications(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
) -> None:
    case_id = open_case(client, heads["officer"], ids).json()["id"]
    act(client, case_id, heads["officer"], "REQUEST_CORRECTION")
    target = inbox(client, heads["admin"])[0]["id"]

    for other in ("other_admin", "officer"):
        denied = client.post(
            f"/api/v1/notifications/{target}/read", headers=heads[other]
        )
        assert denied.status_code == 404
    assert (
        client.post(
            "/api/v1/notifications/00000000-0000-0000-0000-000000000000/read",
            headers=heads["admin"],
        ).status_code
        == 404
    )
    # The failed attempts did not mark it read, and read-all is also per user.
    client.post("/api/v1/notifications/read-all", headers=heads["other_admin"])
    assert inbox(client, heads["admin"], unread="true")[0]["id"] == target


def test_roles_and_authentication(
    client: TestClient, heads: dict[str, dict[str, str]]
) -> None:
    for path in ("", "/unread-count"):
        assert client.get(f"/api/v1/notifications{path}").status_code == 401
        denied = client.get(f"/api/v1/notifications{path}", headers=heads["manager"])
        assert denied.status_code == 403
    manager = heads["manager"]
    assert (
        client.post("/api/v1/notifications/read-all", headers=manager).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/notifications/00000000-0000-0000-0000-000000000000/read",
            headers=manager,
        ).status_code
        == 403
    )


def overdue_case(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    days: int = 1,
) -> str:
    due = datetime.now(UTC) - timedelta(days=days)
    return str(
        open_case(client, heads["officer"], ids, due_at=due.isoformat()).json()["id"]
    )


def test_overdue_notification_is_lazy_and_idempotent(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    case_id = overdue_case(client, heads, ids)
    assert rows(seeded_session, kind="CASE_OVERDUE") == []

    first = inbox(client, heads["officer"])
    second = inbox(client, heads["officer"])
    assert [n["kind"] for n in first] == ["CASE_OVERDUE"]
    assert [n["id"] for n in first] == [n["id"] for n in second]
    client.get("/api/v1/notifications/unread-count", headers=heads["officer"])
    created = rows(seeded_session, kind="CASE_OVERDUE")
    assert len(created) == 1
    assert str(created[0].case_id) == case_id
    assert created[0].dedupe_key is not None
    assert created[0].dedupe_key.startswith(f"overdue:{case_id}:")
    assert (
        client.get(
            "/api/v1/notifications/unread-count", headers=heads["officer"]
        ).json()["unread"]
        == 1
    )
    # Institution admins are not told about the officers' internal deadlines.
    assert inbox(client, heads["admin"]) == []

    # A new due date that also lapses is a new, separately deduplicated alert.
    act(
        client,
        case_id,
        heads["officer"],
        "UPDATED",
        due_at=(datetime.now(UTC) - timedelta(hours=3)).isoformat(),
    )
    inbox(client, heads["officer"])
    inbox(client, heads["officer"])
    assert len(rows(seeded_session, kind="CASE_OVERDUE")) == 2


def test_overdue_targets_assignee_or_all_officers_and_skips_finished(
    client: TestClient,
    heads: dict[str, dict[str, str]],
    ids: list[str],
    seeded_session: Session,
) -> None:
    second = add_officer(seeded_session, "second_officer")
    assigned = overdue_case(client, heads, ids)
    act(client, assigned, heads["officer"], "ASSIGNED", assigned_to=str(second.id))
    unassigned = overdue_case(client, heads, ids, days=2)
    finished = overdue_case(client, heads, ids, days=3)
    act(client, finished, heads["officer"], "START_REVIEW")
    act(client, finished, heads["officer"], "RESOLVED", **REASON)

    inbox(client, heads["officer"])
    ensure_overdue_notifications(seeded_session, second)
    ensure_overdue_notifications(seeded_session, second)

    def cases_for(user: Any) -> set[str]:
        return {
            str(n.case_id)
            for n in rows(seeded_session, kind="CASE_OVERDUE", recipient_user_id=user)
        }

    assert cases_for(user_id(seeded_session, "demo_officer")) == {unassigned}
    assert cases_for(second.id) == {assigned, unassigned}
    assert (
        seeded_session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.kind == "CASE_OVERDUE")
        )
        == 3
    )
