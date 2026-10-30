"""Append-only officer decisions on rule-generated review prompts."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

Decision = Literal["FALSE_POSITIVE", "CONFIRMED_CONCERN", "NEEDS_FOLLOW_UP"]


class IntegrityDecision(Base):
    __tablename__ = "integrity_decisions"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('FALSE_POSITIVE', 'CONFIRMED_CONCERN', 'NEEDS_FOLLOW_UP')",
            name="ck_integrity_decision",
        ),
        CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_integrity_reason"
        ),
        CheckConstraint(
            "char_length(signal_key) BETWEEN 1 AND 300", name="ck_integrity_key"
        ),
        Index(
            "ix_integrity_decision_key_time",
            "institution_id",
            "signal_key",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"))
    signal_key: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
