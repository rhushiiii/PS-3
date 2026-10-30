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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApaarVerification(Base):
    __tablename__ = "apaar_verifications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_verification_record_batch",
        ),
        CheckConstraint(
            "status IN ('SIMULATED_MATCH', 'SIMULATED_MISMATCH', 'PENDING', "
            "'SOURCE_UNAVAILABLE', 'SOURCE_TIMEOUT')",
            name="ck_verification_status",
        ),
        Index("ix_verification_record_time", "record_version_id", "requested_at", "id"),
        Index(
            "uq_verification_idempotency",
            "record_version_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    record_version_id: Mapped[UUID]
    batch_id: Mapped[UUID]
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    adapter_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    external_reference: Mapped[str | None] = mapped_column(String(128))
    evidence_json_redacted: Mapped[dict[str, Any]] = mapped_column(JSONB)
    consent_ref: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(120))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Opaque per-attempt id, null only for rows created before migration 0012.
    provider_request_id: Mapped[str | None] = mapped_column(String(64))
    retry_of_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("apaar_verifications.id")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    request_fingerprint: Mapped[str | None] = mapped_column(String(64))
