from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.audit.services import redact
from app.modules.auth.models import User
from app.seed import seed_id

Headers = Callable[[str], dict[str, str]]
BASE = "/api/v1/audit"
CEDAR = seed_id("institutions", "cedar")
T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def user_id(session: Session, alias: str) -> UUID:
    found = session.scalar(select(User.id).where(User.demo_alias == alias))
    assert found is not None
    return found


def add_event(
    session: Session,
    *,
    action: str = "TEST_ACTION",
    entity_type: str = "test_entity",
    actor: UUID | None = None,
    institution: UUID | None = None,
    occurred_at: datetime = T0,
    details: dict[str, Any] | None = None,
) -> UUID:
    event = AuditEvent(
        id=uuid4(),
        actor_id=actor,
        institution_id=institution,
        action=action,
        entity_type=entity_type,
        entity_id=uuid4(),
        occurred_at=occurred_at,
        metadata_redacted=details or {"source_label": "DEMO"},
    )
    session.add(event)
    session.flush()
    return event.id


def listing(
    client: TestClient, headers: dict[str, str], **params: Any
) -> dict[str, Any]:
    response = client.get(f"{BASE}/events", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.mark.parametrize("path", ["/events", "/actions", f"/events/{uuid4()}"])
def test_only_officers_may_read_the_audit_log(
    client: TestClient, auth_headers: Headers, path: str
) -> None:
    assert client.get(BASE + path).status_code == 401
    for alias in ("demo_manager", "cedar_admin", "demo_verifier"):
        denied = client.get(BASE + path, headers=auth_headers(alias))
        assert denied.status_code == 403, alias
        assert denied.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert client.get(
        BASE + path, headers=auth_headers("demo_officer")
    ).status_code in (
        200,
        404,
    )


def test_filters_ordering_and_pagination(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    actor = user_id(seeded_session, "demo_officer_2")
    ids = [
        add_event(
            seeded_session,
            action="ALPHA" if i % 2 == 0 else "BETA",
            entity_type="widget" if i < 3 else "gadget",
            actor=actor if i < 4 else None,
            institution=CEDAR if i == 0 else None,
            occurred_at=T0 + timedelta(hours=i),
        )
        for i in range(6)
    ]
    mine = {"entity_type": "widget"} | {"from": T0.isoformat()}
    widgets = listing(client, officer, **mine)
    assert widgets["pagination"]["total"] == 3
    # Newest first.
    assert [e["id"] for e in widgets["data"]] == [
        str(i) for i in (ids[2], ids[1], ids[0])
    ]
    assert (
        listing(client, officer, action="ALPHA", entity_type="gadget")["pagination"][
            "total"
        ]
        == 1
    )
    assert (
        listing(client, officer, actor_user_id=str(actor))["pagination"]["total"] == 4
    )
    only_cedar = listing(client, officer, institution_id=str(CEDAR))["data"]
    assert [e["id"] for e in only_cedar][-1] == str(ids[0])

    window = listing(
        client,
        officer,
        **{
            "from": (T0 + timedelta(hours=2)).isoformat(),
            "to": (T0 + timedelta(hours=4)).isoformat(),
            "entity_type": "widget",
        },
    )
    assert [e["id"] for e in window["data"]] == [str(ids[2])]
    inclusive = listing(
        client,
        officer,
        **{
            "from": (T0 + timedelta(hours=3)).isoformat(),
            "to": (T0 + timedelta(hours=3)).isoformat(),
        },
    )
    assert [e["id"] for e in inclusive["data"]] == [str(ids[3])]

    first = listing(client, officer, action="ALPHA", page_size=2, page=1)
    second = listing(client, officer, action="ALPHA", page_size=2, page=2)
    assert first["pagination"] == {"page": 1, "page_size": 2, "total": 3}
    assert len(first["data"]) == 2 and len(second["data"]) == 1
    assert first["data"][0]["occurred_at"] > first["data"][1]["occurred_at"]
    paged_ids = [e["id"] for e in first["data"] + second["data"]]
    assert paged_ids == [str(ids[4]), str(ids[2]), str(ids[0])]
    assert listing(client, officer, action="ALPHA", page_size=2, page=3)["data"] == []


def test_ties_are_ordered_stably(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    for _ in range(5):
        add_event(seeded_session, action="TIE", occurred_at=T0)
    seen = [e["id"] for e in listing(client, officer, action="TIE")["data"]]
    assert seen == sorted(seen, reverse=True)
    one_by_one = [
        listing(client, officer, action="TIE", page_size=1, page=p)["data"][0]["id"]
        for p in range(1, 6)
    ]
    assert one_by_one == seen


def test_invalid_parameters(client: TestClient, auth_headers: Headers) -> None:
    officer = auth_headers("demo_officer")
    for params in (
        {"page_size": 101},
        {"page_size": 0},
        {"page": 0},
        {"actor_user_id": "nope"},
        {"from": "2026-01-01T00:00:00"},  # naive timestamps are ambiguous
        {"from": "2026-02-01T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
    ):
        response = client.get(f"{BASE}/events", headers=officer, params=params)
        assert response.status_code == 422, params
        assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert listing(client, officer, page_size=100)["pagination"]["page_size"] == 100


def test_actions_are_distinct_and_sorted(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    for action in ("ZED_ACTION", "ZED_ACTION", "AAA_ACTION"):
        add_event(seeded_session, action=action)
    body = client.get(f"{BASE}/actions", headers=auth_headers("demo_officer")).json()
    assert body["data"] == sorted(set(body["data"]))
    assert {"AAA_ACTION", "ZED_ACTION", "DEMO_SEED"} <= set(body["data"])


def test_actor_has_role_and_alias_but_no_email(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    actor = user_id(seeded_session, "cedar_admin")
    event = add_event(seeded_session, actor=actor, institution=CEDAR)
    system = add_event(seeded_session)
    detail = client.get(f"{BASE}/events/{event}", headers=officer)
    assert detail.status_code == 200
    body = detail.json()
    assert body["actor"] == {
        "user_id": str(actor),
        "role": "INSTITUTION_ADMIN",
        "display_name": "cedar_admin",
    }
    assert body["institution_id"] == str(CEDAR) and body["action"] == "TEST_ACTION"
    assert "@" not in detail.text and "email" not in detail.text
    assert (
        client.get(f"{BASE}/events/{system}", headers=officer).json()["actor"] is None
    )
    missing = client.get(f"{BASE}/events/{uuid4()}", headers=officer)
    assert missing.status_code == 404
    assert client.get(f"{BASE}/events/not-a-uuid", headers=officer).status_code == 422


def test_details_are_redacted_on_list_and_detail(
    client: TestClient, auth_headers: Headers, seeded_session: Session
) -> None:
    officer = auth_headers("demo_officer")
    leaked = "900000000123"
    event = add_event(
        seeded_session,
        action="REDACTION_CHECK",
        details={
            "note": f"value {leaked} end",
            "count": "3",
            "apaar_id": leaked,
            "Access_Token": "synthetic-token",
            "password": "synthetic",
            "client_secret": "synthetic",
            "match_key": "synthetic",
            "short": "12345678901",  # 11 digits stay visible
        },
    )
    listed = next(
        e
        for e in listing(client, officer, action="REDACTION_CHECK")["data"]
        if e["id"] == str(event)
    )
    detail = client.get(f"{BASE}/events/{event}", headers=officer)
    for details, text in (
        (listed["details"], str(listed)),
        (detail.json()["details"], detail.text),
    ):
        assert leaked not in text
        assert details == {
            "note": "value [MASKED] end",
            "count": "3",
            "short": "12345678901",
        }
    assert "apaar" not in detail.text.lower() and "synthetic-token" not in detail.text


def test_redact_handles_nested_and_numeric_values() -> None:
    assert redact(
        {
            "a": [{"apaar": "x", "ok": "1234567890123"}, 900000000123, 7, True, None],
            "nested": {"api_key": "x", "n": "no digits"},
        }
    ) == {
        "a": [{"ok": "[MASKED]"}, "[MASKED]", 7, True, None],
        "nested": {"n": "no digits"},
    }


def test_real_application_events_are_exposed_without_pii(
    client: TestClient, auth_headers: Headers
) -> None:
    officer = auth_headers("demo_officer")
    body = listing(client, officer, action="DEMO_SEED", page_size=100)
    assert body["pagination"]["total"] > 0
    assert all(e["details"]["source_label"] == "DEMO" for e in body["data"])
    assert "@" not in str(body)
