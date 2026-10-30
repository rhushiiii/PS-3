from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.modules.auth.models import Role


class AuditActor(BaseModel):
    """No email: only the role and demo alias identify who acted."""

    user_id: UUID
    role: Role | None
    display_name: str


class AuditEventResponse(BaseModel):
    id: UUID
    occurred_at: datetime
    actor: AuditActor | None
    action: str
    entity_type: str
    entity_id: UUID
    institution_id: UUID | None
    details: dict[str, Any]


class AuditActionsResponse(BaseModel):
    data: list[str]


@dataclass(frozen=True)
class AuditFilters:
    actor_user_id: UUID | None = None
    action: str | None = None
    entity_type: str | None = None
    institution_id: UUID | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
