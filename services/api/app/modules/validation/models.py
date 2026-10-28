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
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ValidationRun(Base):
    __tablename__ = "validation_runs"
    __table_args__ = (
        UniqueConstraint("id", "batch_id", name="uq_validation_run_batch"),
        CheckConstraint(
            "kind IN ('INITIAL', 'REVALIDATION')", name="ck_validation_kind"
        ),
        Index(
            "uq_validation_initial",
            "batch_id",
            unique=True,
            postgresql_where=text("kind = 'INITIAL'"),
        ),
        Index("ix_validation_batch_time", "batch_id", "evaluated_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(ForeignKey("submission_batches.id"))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(16))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ruleset_version: Mapped[str] = mapped_column(String(64))
    ruleset_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    compared_scope_revisions_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ValidationFinding(Base):
    __tablename__ = "validation_findings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["run_id", "batch_id"],
            ["validation_runs.id", "validation_runs.batch_id"],
            name="fk_finding_run_batch",
        ),
        ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_finding_record_batch",
        ),
        UniqueConstraint("run_id", "ordinal", name="uq_finding_ordinal"),
        CheckConstraint("ordinal > 0", name="ck_finding_ordinal"),
        CheckConstraint(
            "severity IN ('ERROR', 'WARNING', 'INFO')", name="ck_finding_severity"
        ),
        CheckConstraint(
            "classification IN ('ACTIVATION_BLOCKING', 'REVIEWABLE')",
            name="ck_finding_classification",
        ),
        Index("ix_finding_record", "run_id", "record_version_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID]
    batch_id: Mapped[UUID]
    record_version_id: Mapped[UUID | None]
    ordinal: Mapped[int]
    rule_code: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    classification: Mapped[str] = mapped_column(String(32))
    field_name: Mapped[str | None] = mapped_column(String(64))
    explanation: Mapped[str] = mapped_column(Text)
    evidence_json_redacted: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
