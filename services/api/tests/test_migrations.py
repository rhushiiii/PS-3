import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.database import Base
from app.modules.auth.models import Role, User
from app.modules.institutions.models import AdmissionCategory, IntakeRule, Programme
from app.seed import seed_id


def test_migration_roundtrip_and_metadata(
    db_engine: Engine, migration_config: Config, postgres_url: str
) -> None:
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.downgrade(migration_config, "base")
        assert set(inspect(db_engine).get_table_names()) == {"alembic_version"}
        command.upgrade(migration_config, "head")
        command.check(migration_config)
    assert set(inspect(db_engine).get_table_names()) == {
        "alembic_version",
        "institutions",
        "programmes",
        "intake_rules",
        "users",
        "audit_events",
        "submission_scopes",
        "submission_batches",
        "student_record_versions",
        "validation_runs",
        "validation_findings",
        "submission_reviews",
        "apaar_verifications",
        "review_cases",
        "case_records",
        "case_events",
    }
    with db_engine.connect() as connection:
        assert (
            compare_metadata(MigrationContext.configure(connection), Base.metadata)
            == []
        )


@pytest.mark.parametrize("bad_field", ["institution", "capacity", "category", "year"])
def test_intake_constraints(seeded_session: Session, bad_field: str) -> None:
    values: dict[str, object] = {
        "id": uuid4(),
        "institution_id": seed_id("institutions", "cedar"),
        "programme_id": seed_id("programmes", "cedar/DEMO-COMP"),
        "academic_year": "2026-27",
        "category": AdmissionCategory.REGULAR,
        "approved_seats": 3,
        "rule_version": "constraint-test",
        "source_label": "DEMO",
    }
    if bad_field == "institution":
        values["institution_id"] = seed_id("institutions", "maple")
    elif bad_field == "capacity":
        values["approved_seats"] = -1
    elif bad_field == "category":
        values["category"] = "UNSUPPORTED"
    else:
        values["academic_year"] = "invalid"
    with pytest.raises(IntegrityError), seeded_session.begin_nested():
        seeded_session.add(IntakeRule(**values))
        seeded_session.flush()


def test_admin_requires_institution(seeded_session: Session) -> None:
    with pytest.raises(IntegrityError), seeded_session.begin_nested():
        seeded_session.add(
            User(
                email="constraint@sih26263.invalid",
                role=Role.INSTITUTION_ADMIN,
                institution_id=None,
                is_demo=True,
            )
        )
        seeded_session.flush()


def test_programme_code_unique_within_institution(seeded_session: Session) -> None:
    with pytest.raises(IntegrityError), seeded_session.begin_nested():
        seeded_session.add(
            Programme(
                institution_id=seed_id("institutions", "cedar"),
                code="DEMO-COMP",
                name="Duplicate synthetic programme",
            )
        )
        seeded_session.flush()
