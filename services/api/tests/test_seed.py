from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.audit.models import AuditEvent
from app.modules.auth.models import User
from app.modules.institutions.models import Institution, IntakeRule, Programme
from app.seed import SeedConflict, main, seed_demo, seed_id


def test_deterministic_seed_and_no_duplicate_audits(
    db_session: Session, demo_settings: Settings
) -> None:
    assert seed_demo(db_session, demo_settings)["created"] == 46
    db_session.flush()
    first_ids = set(db_session.scalars(select(AuditEvent.id)))
    assert len(first_ids) == 46
    assert seed_demo(db_session, demo_settings)["created"] == 0
    db_session.flush()
    assert set(db_session.scalars(select(AuditEvent.id))) == first_ids
    for model, count in ((Institution, 3), (Programme, 6), (IntakeRule, 30), (User, 7)):
        assert db_session.scalar(select(func.count()).select_from(model)) == count
    assert all(
        user.email.endswith(".invalid") for user in db_session.scalars(select(User))
    )
    assert all(user.password_hash is None for user in db_session.scalars(select(User)))
    for event in db_session.scalars(select(AuditEvent)):
        assert event.actor_id is None
        assert event.metadata_redacted == {
            "actor_kind": "SYSTEM",
            "source_label": "DEMO",
        }
        assert event.occurred_at.tzinfo is not None


def test_seed_conflict_rolls_back_partial_work(
    db_session: Session, demo_settings: Settings
) -> None:
    db_session.add(
        Institution(
            id=seed_id("institutions", "maple"),
            permanent_id="DEMO-INST-002",
            name="Conflicting synthetic name",
            region="DEMO_REGION_2",
            active=True,
        )
    )
    db_session.flush()
    with pytest.raises(SeedConflict), db_session.begin_nested():
        seed_demo(db_session, demo_settings)
    assert db_session.scalar(select(func.count()).select_from(Institution)) == 1
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_seed_does_not_reactivate_identity(
    seeded_session: Session, demo_settings: Settings
) -> None:
    user = seeded_session.get(User, seed_id("users", "cedar_admin"))
    assert user is not None
    user.active = False
    seeded_session.flush()
    with pytest.raises(SeedConflict), seeded_session.begin_nested():
        seed_demo(seeded_session, demo_settings)
    assert not user.active


def test_seed_cli_denied_without_demo_mode(settings: Settings) -> None:
    with (
        patch("app.seed.Settings", return_value=settings),
        patch("app.seed.build_engine") as engine,
    ):
        assert main() == 1
        engine.assert_not_called()
