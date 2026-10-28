from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CASE_STATUSES = (
    "OPEN",
    "AWAITING_CORRECTION",
    "UNDER_REVIEW",
    "RESOLVED",
    "CLOSED",
)
CASE_CATEGORIES = (
    "POTENTIAL_DUPLICATE",
    "APAAR_MISMATCH",
    "INTAKE_DISCREPANCY",
    "OTHER",
)
CASE_EVENT_ACTIONS = (
    "OPENED",
    "COMMENT",
    "REQUEST_CORRECTION",
    "CORRECTION_RECEIVED",
    "ASSIGNED",
    "RESOLVED",
    "CLOSED",
)


class ReviewCase(Base):
    __tablename__ = "review_cases"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN', 'AWAITING_CORRECTION', 'UNDER_REVIEW', 'RESOLVED', "
            "'CLOSED')",
            name="ck_case_status",
        ),
        CheckConstraint(
            "category IN ('POTENTIAL_DUPLICATE', 'APAAR_MISMATCH', "
            "'INTAKE_DISCREPANCY', 'OTHER')",
            name="ck_case_category",
        ),
        Index("ix_case_institution_status", "institution_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"))
    opened_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), server_default="OPEN")
    category: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseRecord(Base):
    __tablename__ = "case_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_case_record_batch",
        ),
        UniqueConstraint("case_id", "record_version_id", name="uq_case_record"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("review_cases.id"))
    record_version_id: Mapped[UUID]
    batch_id: Mapped[UUID]
    linked_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CaseEvent(Base):
    __tablename__ = "case_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('OPENED', 'COMMENT', 'REQUEST_CORRECTION', "
            "'CORRECTION_RECEIVED', 'ASSIGNED', 'RESOLVED', 'CLOSED')",
            name="ck_case_event_action",
        ),
        Index("ix_case_event_case_ordinal", "case_id", "ordinal"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Globally monotonic, DB-assigned; (created_at, random id) cannot reliably
    # order two events recorded within the same timestamp tick.
    ordinal: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("review_cases.id"))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(Text)
    linked_batch_id: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
