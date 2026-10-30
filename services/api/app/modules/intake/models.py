"""Append-only intake governance records. All values are DEMO, never official."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def clock() -> Any:
    # clock_timestamp() keeps same-transaction rows ordered (now() would tie).
    return func.clock_timestamp()


class IntakeRuleChange(Base):
    __tablename__ = "intake_rule_changes"
    __table_args__ = (
        CheckConstraint(
            "old_approved_seats >= 0 AND new_approved_seats >= 0",
            name="ck_rule_change_seats",
        ),
        CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_rule_change_reason"
        ),
        Index("ix_rule_change_rule_time", "intake_rule_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    intake_rule_id: Mapped[UUID] = mapped_column(ForeignKey("intake_rules.id"))
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    old_approved_seats: Mapped[int]
    new_approved_seats: Mapped[int]
    old_rule_version: Mapped[str] = mapped_column(String(64))
    new_rule_version: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=clock()
    )


class IntakeDeclaration(Base):
    __tablename__ = "intake_declarations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["programme_id", "institution_id"],
            ["programmes.id", "programmes.institution_id"],
            name="fk_declaration_programme_institution",
        ),
        CheckConstraint("declared_total >= 0", name="ck_declaration_total"),
        CheckConstraint(
            "academic_year ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_declaration_year"
        ),
        CheckConstraint(
            "char_length(basis) BETWEEN 1 AND 500", name="ck_declaration_basis"
        ),
        Index(
            "ix_declaration_scope_time",
            "institution_id",
            "programme_id",
            "academic_year",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID]
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    declared_total: Mapped[int]
    source_label: Mapped[str] = mapped_column(String(32), server_default=text("'DEMO'"))
    basis: Mapped[str] = mapped_column(String(500))
    declared_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=clock()
    )


class IntakeAssessment(Base):
    __tablename__ = "intake_assessments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["batch_id", "institution_id", "programme_id", "academic_year"],
            [
                "submission_batches.id",
                "submission_batches.institution_id",
                "submission_batches.programme_id",
                "submission_batches.academic_year",
            ],
            name="fk_assessment_batch_context",
        ),
        CheckConstraint("scope_revision >= 0", name="ck_assessment_revision"),
        Index("ix_assessment_batch_time", "batch_id", "computed_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID]
    institution_id: Mapped[UUID]
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    scope_revision: Mapped[int]
    current_batch_id: Mapped[UUID | None]
    computed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=clock()
    )
    rule_version: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
