from datetime import datetime
from typing import Any, Literal, get_args
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

# Single source of truth: schemas import these literals; CHECK constraints derive
# from them so the database, API and services cannot drift apart.
CaseStatus = Literal[
    "OPEN",
    "ASSIGNED",
    "UNDER_REVIEW",
    "AWAITING_CORRECTION",
    "RESPONSE_SUBMITTED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
]
CaseCategory = Literal[
    "POTENTIAL_DUPLICATE", "APAAR_MISMATCH", "INTAKE_DISCREPANCY", "OTHER"
]
CasePriority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
CaseSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
CaseEventAction = Literal[
    "OPENED",
    "COMMENT",
    "REQUEST_CORRECTION",
    "CORRECTION_RECEIVED",
    "ASSIGNED",
    "START_REVIEW",
    "RESPONSE_SUBMITTED",
    "UPDATED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
]
CLOSED_STATUSES = ("RESOLVED", "REJECTED", "CLOSED")


def one_of(column: str, literal: Any) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in get_args(literal))})"


class ReviewCase(Base):
    __tablename__ = "review_cases"
    __table_args__ = (
        CheckConstraint(one_of("status", CaseStatus), name="ck_case_status"),
        CheckConstraint(one_of("category", CaseCategory), name="ck_case_category"),
        CheckConstraint(one_of("priority", CasePriority), name="ck_case_priority"),
        CheckConstraint(one_of("severity", CaseSeverity), name="ck_case_severity"),
        CheckConstraint(
            "resolution_reason IS NULL OR char_length(resolution_reason) <= 2000",
            name="ck_case_resolution_reason",
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
    priority: Mapped[str] = mapped_column(String(16), server_default="MEDIUM")
    severity: Mapped[str] = mapped_column(String(16), server_default="MEDIUM")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_reason: Mapped[str | None] = mapped_column(Text)


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
        CheckConstraint(one_of("action", CaseEventAction), name="ck_case_event_action"),
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
