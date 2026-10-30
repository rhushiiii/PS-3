import re
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.http import APIError
from app.core.pagination import Page, Pagination
from app.modules.audit.models import AuditEvent
from app.modules.audit.schemas import AuditActor, AuditEventResponse, AuditFilters
from app.modules.auth.models import Role, User


def record_action(
    session: Session,
    *,
    actor_id: UUID | None,
    institution_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    event_id: UUID | None = None,
    details: dict[str, str] | None = None,
) -> None:
    # Fixed metadata shape prevents callers accidentally retaining request bodies.
    session.add(
        AuditEvent(
            id=event_id,
            actor_id=actor_id,
            institution_id=institution_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_redacted={
                "actor_kind": "USER" if actor_id else "SYSTEM",
                "source_label": "DEMO",
                # Optional non-PII scalars only (counts, versions); never APAAR.
                **(details or {}),
            },
        )
    )


# ------------------------------------------------------------------ explorer reads

APAAR_RUN = re.compile(r"\d{12,}")
FORBIDDEN_KEY = re.compile(r"apaar|token|password|secret|key", re.IGNORECASE)
MASK = "[MASKED]"


def redact(value: Any) -> Any:
    """Second pass after record_action: mask 12+ digit runs, drop risky keys."""
    if isinstance(value, dict):
        return {
            k: redact(v) for k, v in value.items() if not FORBIDDEN_KEY.search(str(k))
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return APAAR_RUN.sub(MASK, value)
    if isinstance(value, int) and not isinstance(value, bool):
        return MASK if APAAR_RUN.search(str(value)) else value
    return value


def to_event(
    event: AuditEvent, role: Role | None, alias: str | None
) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        occurred_at=event.occurred_at,
        actor=(
            AuditActor(
                user_id=event.actor_id,
                role=role,
                display_name=alias or "UNNAMED_USER",
            )
            if event.actor_id is not None
            else None
        ),
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        institution_id=event.institution_id,
        details=redact(event.metadata_redacted),
    )


def event_statement() -> Select[AuditEvent, Role, str | None]:
    return select(AuditEvent, User.role, User.demo_alias).outerjoin(
        User, User.id == AuditEvent.actor_id
    )


def list_events(
    session: Session, filters: AuditFilters, page: int, page_size: int
) -> Page[AuditEventResponse]:
    statement = event_statement()
    for column, value in (
        (AuditEvent.actor_id, filters.actor_user_id),
        (AuditEvent.action, filters.action),
        (AuditEvent.entity_type, filters.entity_type),
        (AuditEvent.institution_id, filters.institution_id),
    ):
        if value is not None:
            statement = statement.where(column == value)
    if filters.occurred_from is not None:
        statement = statement.where(AuditEvent.occurred_at >= filters.occurred_from)
    if filters.occurred_to is not None:
        statement = statement.where(AuditEvent.occurred_at <= filters.occurred_to)
    total = (
        session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        or 0
    )
    rows = session.execute(
        statement.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page[AuditEventResponse](
        data=[to_event(e, r, a) for e, r, a in rows],
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


def get_event(session: Session, event_id: UUID) -> AuditEventResponse:
    row = session.execute(event_statement().where(AuditEvent.id == event_id)).first()
    if row is None:
        raise APIError(404, "RESOURCE_NOT_FOUND", "Resource not found")
    return to_event(row[0], row[1], row[2])


def list_actions(session: Session) -> list[str]:
    return list(
        session.scalars(
            select(AuditEvent.action).distinct().order_by(AuditEvent.action)
        )
    )
