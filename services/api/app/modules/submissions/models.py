from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
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

from app.core.database import Base, Timestamps


class ProcessingStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SubmissionScope(Timestamps, Base):
    __tablename__ = "submission_scopes"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "programme_id",
            "academic_year",
            name="uq_submission_scope",
        ),
        UniqueConstraint(
            "id",
            "institution_id",
            "programme_id",
            "academic_year",
            name="uq_scope_context",
        ),
        ForeignKeyConstraint(
            ["programme_id", "institution_id"],
            ["programmes.id", "programmes.institution_id"],
            name="fk_scope_programme",
        ),
        ForeignKeyConstraint(
            ["current_batch_id", "id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_scope_current_batch",
            use_alter=True,
        ),
        CheckConstraint("revision >= 0", name="ck_scope_revision"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    institution_id: Mapped[UUID]
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    current_batch_id: Mapped[UUID | None]
    revision: Mapped[int] = mapped_column(server_default="0")


class SubmissionBatch(Base):
    __tablename__ = "submission_batches"
    __table_args__ = (
        ForeignKeyConstraint(
            ["scope_id", "institution_id", "programme_id", "academic_year"],
            [
                "submission_scopes.id",
                "submission_scopes.institution_id",
                "submission_scopes.programme_id",
                "submission_scopes.academic_year",
            ],
            name="fk_batch_scope_context",
        ),
        UniqueConstraint("id", "scope_id", name="uq_batch_scope"),
        UniqueConstraint(
            "id",
            "institution_id",
            "programme_id",
            "academic_year",
            name="uq_batch_context",
        ),
        ForeignKeyConstraint(
            ["base_batch_id", "scope_id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_batch_base",
        ),
        CheckConstraint(
            "row_count > 0 AND file_size_bytes > 0 AND base_scope_revision >= 0",
            name="ck_batch_counts",
        ),
        CheckConstraint("submission_mode = 'SNAPSHOT'", name="ck_batch_mode"),
        ForeignKeyConstraint(
            ["activation_review_id", "id"],
            ["submission_reviews.id", "submission_reviews.batch_id"],
            name="fk_batch_activation_review",
            use_alter=True,
        ),
        CheckConstraint(
            "(activated_at IS NULL) = (activation_review_id IS NULL)",
            name="ck_batch_activation_pair",
        ),
        Index(
            "uq_batch_idempotency",
            "institution_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scope_id: Mapped[UUID] = mapped_column(index=True)
    institution_id: Mapped[UUID] = mapped_column(index=True)
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(Text)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    file_size_bytes: Mapped[int]
    row_count: Mapped[int]
    source: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(16))
    submission_mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(
            ProcessingStatus,
            native_enum=False,
            create_constraint=True,
            name="processing_status",
        )
    )
    base_batch_id: Mapped[UUID | None]
    base_scope_revision: Mapped[int]
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_review_id: Mapped[UUID | None]
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    idempotency_fingerprint: Mapped[str | None] = mapped_column(String(64))


class SubmissionReview(Base):
    __tablename__ = "submission_reviews"
    __table_args__ = (
        UniqueConstraint("id", "batch_id", name="uq_review_batch"),
        ForeignKeyConstraint(
            ["batch_id", "scope_id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_review_batch_scope",
        ),
        ForeignKeyConstraint(
            ["validation_run_id", "batch_id"],
            ["validation_runs.id", "validation_runs.batch_id"],
            name="fk_review_run_batch",
        ),
        ForeignKeyConstraint(
            ["expected_current_batch_id", "scope_id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_review_current_scope",
        ),
        CheckConstraint("expected_scope_revision >= 0", name="ck_review_revision"),
        Index("ix_review_batch_time", "batch_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID]
    scope_id: Mapped[UUID]
    validation_run_id: Mapped[UUID]
    reviewed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expected_scope_revision: Mapped[int]
    expected_current_batch_id: Mapped[UUID | None]
    review_policy_version: Mapped[str] = mapped_column(String(64))
    review_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB)


class StudentRecordVersion(Base):
    __tablename__ = "student_record_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["batch_id", "institution_id", "programme_id", "academic_year"],
            [
                "submission_batches.id",
                "submission_batches.institution_id",
                "submission_batches.programme_id",
                "submission_batches.academic_year",
            ],
            name="fk_record_batch_context",
        ),
        UniqueConstraint("batch_id", "source_row_number", name="uq_record_source"),
        UniqueConstraint("id", "batch_id", name="uq_record_batch"),
        CheckConstraint("source_row_number >= 2", name="ck_record_source"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(index=True)
    source_row_number: Mapped[int]
    institution_id: Mapped[UUID] = mapped_column(index=True)
    programme_id: Mapped[UUID]
    academic_year: Mapped[str] = mapped_column(String(7))
    college_student_id: Mapped[str] = mapped_column(Text)
    full_name_demo: Mapped[str] = mapped_column(Text)
    apaar_identifier_encrypted_or_demo_token: Mapped[str] = mapped_column(Text)
    apaar_match_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    admission_category: Mapped[str] = mapped_column(Text)
    enrollment_status: Mapped[str] = mapped_column(Text)
    enrollment_date: Mapped[date | None]
    original_json: Mapped[dict[str, str]] = mapped_column(JSONB)
    normalized_json: Mapped[dict[str, str]] = mapped_column(JSONB)
