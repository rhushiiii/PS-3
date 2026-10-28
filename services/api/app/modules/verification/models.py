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
            "'SOURCE_UNAVAILABLE')",
            name="ck_verification_status",
        ),
        Index("ix_verification_record_time", "record_version_id", "requested_at", "id"),
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
