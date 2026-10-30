import csv
import io
import os
import re
from collections.abc import Callable, Iterator
from datetime import datetime
from unittest.mock import patch

import psycopg
import pytest
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy import Engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.database import Base, build_engine, get_session
from app.core.http import utc_now
from app.main import create_app
from app.modules.submissions.activation import get_activation_session
from app.modules.submissions.models import (
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.submissions.parsing import HEADERS
from app.modules.validation.services import get_validation_session
from app.seed import seed_demo


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url=SecretStr(
            "postgresql+psycopg://demo:synthetic-secret@127.0.0.1:1/test"
        ),
        demo_auth=False,
        app_env="production",
    )


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if raw_url is None:
        pytest.skip(
            "Set TEST_DATABASE_URL to a new local sih26263_m1_test_<hex> database"
        )
    url = make_url(raw_url)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or not re.fullmatch(r"sih26263_m1_test_[0-9a-f]{8,32}", url.database or "")
    ):
        raise ValueError("Tests require a new, explicitly named local M1 test database")
    admin_url = url.set(drivername="postgresql", database="postgres")
    database_name = url.database
    assert database_name is not None
    # CREATE must succeed first. Never drop or reuse a pre-existing database.
    with psycopg.connect(
        admin_url.render_as_string(hide_password=False), autocommit=True
    ) as connection:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )
        try:
            yield raw_url
        finally:
            connection.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(database_name))
            )


@pytest.fixture(scope="session")
def migration_config(postgres_url: str) -> Config:
    config = Config("alembic.ini")
    # Alembic's URL comes from Settings; expose only this dedicated test target.
    config.attributes["test_url"] = postgres_url
    return config


@pytest.fixture(scope="session")
def db_engine(postgres_url: str, migration_config: Config) -> Iterator[Engine]:
    with patch.dict(os.environ, {"DATABASE_URL": postgres_url}):
        command.upgrade(migration_config, "head")
    engine = build_engine(
        Settings(
            _env_file=None,
            database_url=SecretStr(postgres_url),
            demo_auth=False,
            app_env="production",
        )
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    with db_engine.connect() as connection:
        transaction = connection.begin()
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            yield session
        transaction.rollback()


@pytest.fixture
def demo_settings(postgres_url: str) -> Settings:
    return Settings(
        _env_file=None,
        database_url=SecretStr(postgres_url),
        app_env="local",
        demo_auth=True,
        demo_auth_secret=SecretStr("synthetic-test-key-" + "x" * 32),
        apaar_matching_key=SecretStr("synthetic-matching-key-" + "y" * 32),
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
def seeded_session(db_session: Session, demo_settings: Settings) -> Session:
    seed_demo(db_session, demo_settings)
    db_session.commit()
    return db_session


@pytest.fixture
def application(demo_settings: Settings, seeded_session: Session) -> FastAPI:
    app = create_app(demo_settings)

    def session_override() -> Iterator[Session]:
        yield seeded_session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_validation_session] = session_override
    app.dependency_overrides[get_activation_session] = session_override
    return app


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(
        application, base_url="http://localhost", client=("127.0.0.1", 50000)
    ) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> Callable[[str], dict[str, str]]:
    def login(alias: str) -> dict[str, str]:
        response = client.post("/api/v1/auth/demo-login", json={"demo_alias": alias})
        assert response.status_code == 200, response.text
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    return login


def truncate_all(engine: Engine) -> None:
    """Empty every application table of the dedicated test database."""
    assert (engine.url.database or "").startswith("sih26263_m1_test_")
    names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {names}"))


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
    from test_cases import record_ids  # lazy: test modules import this file
    from test_validation import upload

    return record_ids(seeded_session, upload(client, heads["admin"]))


def counts(session: Session) -> tuple[int, int, int]:
    """Row counts of submission scopes, batches and record versions."""
    values = tuple(
        session.scalar(select(func.count()).select_from(model)) or 0
        for model in (SubmissionScope, SubmissionBatch, StudentRecordVersion)
    )
    return values[0], values[1], values[2]


def pin_clock(application: FastAPI, moment: datetime) -> None:
    """Freeze the `utc_now` request dependency at `moment`."""
    application.dependency_overrides[utc_now] = lambda: moment


def admission_csv(*rows: dict[str, str]) -> bytes:
    """Synthetic admission CSV; each dict overrides the canonical DEMO row."""
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
