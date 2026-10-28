from collections.abc import Iterator
from datetime import datetime
from typing import cast

from fastapi import Request
from sqlalchemy import DateTime, Engine, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    """Feature-owned models will share this migration metadata."""


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def build_engine(settings: Settings) -> Engine:
    # Engine construction is lazy: startup does not contact PostgreSQL.
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
        hide_parameters=True,
    )


def get_engine(request: Request) -> Engine:
    return cast(Engine, request.app.state.engine)


def get_session(request: Request) -> Iterator[Session]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory() as session:
        yield session


def get_snapshot_session(request: Request) -> Iterator[Session]:
    """Consistent reads, isolated from authentication's earlier statements."""
    with (
        get_engine(request)
        .connect()
        .execution_options(isolation_level="REPEATABLE READ") as connection
    ):
        with Session(bind=connection, expire_on_commit=False) as session:
            yield session
