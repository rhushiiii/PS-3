import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, delete, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.database import Base
from app.modules.auth.models import Role, User
from app.modules.cases.models import ReviewCase
from app.modules.institutions.models import (
    AdmissionCategory,
    Institution,
    IntakeRule,
    Programme,
)
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
        "notifications",
        "intake_rule_changes",
        "intake_declarations",
        "intake_assessments",
        "integrity_decisions",
        "admission_credentials",
        "credential_revocations",
        "credential_verifications",
    }
    with db_engine.connect() as connection:
        assert (
            compare_metadata(MigrationContext.configure(connection), Base.metadata)
            == []
        )


def test_intake_governance_migration_roundtrip(
    db_engine: Engine, migration_config: Config, postgres_url: str
) -> None:
    tables = {"intake_rule_changes", "intake_declarations", "intake_assessments"}
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.downgrade(migration_config, "0009_notifications")
        names = set(inspect(db_engine).get_table_names())
        assert not tables & names and "notifications" in names
        with db_engine.connect() as connection:
            assert not connection.execute(
                text(
                    "SELECT 1 FROM pg_proc "
                    "WHERE proname = 'prevent_intake_history_mutation'"
                )
            ).all()
        command.upgrade(migration_config, "head")
        assert tables <= set(inspect(db_engine).get_table_names())
        with db_engine.connect() as connection:
            triggers = connection.execute(
                text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
            ).scalars()
            assert {f"{table}_immutable" for table in tables} <= set(triggers)


def test_integrity_decisions_migration_roundtrip(
    db_engine: Engine, migration_config: Config, postgres_url: str
) -> None:
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.downgrade(migration_config, "0010_intake_governance")
        assert "integrity_decisions" not in inspect(db_engine).get_table_names()
        with db_engine.connect() as connection:
            # The shared trigger function belongs to 0010 and must survive.
            assert connection.execute(
                text(
                    "SELECT 1 FROM pg_proc "
                    "WHERE proname = 'prevent_intake_history_mutation'"
                )
            ).all()
        command.upgrade(migration_config, "head")
        assert "integrity_decisions" in inspect(db_engine).get_table_names()
        with db_engine.connect() as connection:
            triggers = connection.execute(
                text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
            ).scalars()
            assert "integrity_decisions_immutable" in set(triggers)
        indexes = {
            i["name"] for i in inspect(db_engine).get_indexes("integrity_decisions")
        }
        assert "ix_integrity_decision_key_time" in indexes
        command.check(migration_config)


def test_case_workflow_migration_downgrade_guard(
    db_engine: Engine, migration_config: Config, postgres_url: str
) -> None:
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.downgrade(migration_config, "0007_upload_idempotency")
        columns = {c["name"] for c in inspect(db_engine).get_columns("review_cases")}
        assert not columns & {"priority", "severity", "due_at", "resolution_reason"}
        assert "notifications" not in inspect(db_engine).get_table_names()
        command.upgrade(migration_config, "head")

        institution, officer, case = uuid4(), uuid4(), uuid4()
        with Session(db_engine) as session, session.begin():
            session.add(
                Institution(
                    id=institution,
                    permanent_id=f"DEMO-MIG-{institution.hex[:8]}",
                    name="Demo Migration Institute",
                    region="DEMO_REGION_1",
                )
            )
            session.add(
                User(
                    id=officer,
                    email=f"{officer.hex}@sih26263.invalid",
                    role=Role.AICTE_OFFICER,
                    is_demo=True,
                )
            )
            session.flush()
            session.add(
                ReviewCase(
                    id=case,
                    institution_id=institution,
                    opened_by=officer,
                    status="RESPONSE_SUBMITTED",
                    category="OTHER",
                    summary="Synthetic migration guard",
                )
            )
        try:
            # New statuses cannot be represented by the 0006 constraints, so the
            # downgrade refuses (and rolls back) instead of corrupting history.
            with pytest.raises(RuntimeError, match="Cannot downgrade"):
                command.downgrade(migration_config, "0007_upload_idempotency")
        finally:
            with Session(db_engine) as session, session.begin():
                session.execute(delete(ReviewCase).where(ReviewCase.id == case))
                session.execute(delete(User).where(User.id == officer))
                session.execute(
                    delete(Institution).where(Institution.id == institution)
                )
        command.downgrade(migration_config, "0007_upload_idempotency")
        command.upgrade(migration_config, "head")


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


def test_verification_credentials_migration_roundtrip(
    db_engine: Engine, migration_config: Config, postgres_url: str
) -> None:
    tables = {
        "admission_credentials",
        "credential_revocations",
        "credential_verifications",
    }
    new_columns = {
        "provider_request_id",
        "retry_of_id",
        "idempotency_key",
        "request_fingerprint",
    }
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.downgrade(migration_config, "0011_integrity_decisions")
        assert not tables & set(inspect(db_engine).get_table_names())
        columns = {
            c["name"] for c in inspect(db_engine).get_columns("apaar_verifications")
        }
        assert not columns & new_columns
        command.upgrade(migration_config, "head")
        assert tables <= set(inspect(db_engine).get_table_names())
        columns = {
            c["name"] for c in inspect(db_engine).get_columns("apaar_verifications")
        }
        assert new_columns <= columns
        with db_engine.connect() as connection:
            triggers = set(
                connection.execute(
                    text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
                ).scalars()
            )
            assert {f"{table}_immutable" for table in tables} <= triggers
            assert "apaar_verifications_immutable" in triggers
            heads = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalars()
            assert list(heads) == ["0012_verification_credentials"]
        command.check(migration_config)
