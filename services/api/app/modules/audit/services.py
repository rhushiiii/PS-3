from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


def record_action(
    session: Session,
    *,
    actor_id: UUID | None,
    institution_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    event_id: UUID | None = None,
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
            },
        )
    )
