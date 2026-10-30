from datetime import datetime
from typing import Literal, get_args
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

NotificationKind = Literal[
    "CASE_ASSIGNED",
    "CORRECTION_REQUESTED",
    "RESPONSE_SUBMITTED",
    "CASE_RESOLVED",
    "CASE_REJECTED",
    "CASE_CLOSED",
    "CASE_OVERDUE",
]


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "kind IN ("
            + ", ".join(repr(kind) for kind in get_args(NotificationKind))
            + ")",
            name="ck_notification_kind",
        ),
        Index(
            "ix_notification_recipient_read",
            "recipient_user_id",
            "read_at",
            "created_at",
        ),
        Index(
            "uq_notification_dedupe",
            "recipient_user_id",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recipient_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    institution_id: Mapped[UUID | None] = mapped_column(ForeignKey("institutions.id"))
    kind: Mapped[str] = mapped_column(String(32))
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("review_cases.id"))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    dedupe_key: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
