from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.notifications.models import NotificationKind


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: NotificationKind
    case_id: UUID | None
    institution_id: UUID | None
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None


class UnreadCountResponse(BaseModel):
    unread: int


class ReadAllResponse(BaseModel):
    marked_read: int
