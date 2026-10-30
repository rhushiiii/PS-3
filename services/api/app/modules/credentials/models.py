from datetime import datetime
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


class AdmissionCredential(Base):
    """Issued-credential metadata. The signed token itself is never stored."""

    __tablename__ = "admission_credentials"
    __table_args__ = (
        CheckConstraint("expires_at > issued_at", name="ck_credential_expiry"),
        Index("ix_credential_institution_time", "institution_id", "issued_at", "id"),
    )

    # The credential id is the token's jti.
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    record_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_record_versions.id"), index=True
    )
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id"))
    issued_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    kid: Mapped[str] = mapped_column(String(64))
    claims_sha256: Mapped[str] = mapped_column(String(64))
    source_label: Mapped[str] = mapped_column(String(16), server_default="DEMO")


class CredentialRevocation(Base):
    __tablename__ = "credential_revocations"
    __table_args__ = (
        CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_revocation_reason"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    credential_id: Mapped[UUID] = mapped_column(
        ForeignKey("admission_credentials.id"), unique=True
    )
    revoked_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )


class CredentialVerification(Base):
    """Access log of verification attempts; never contains the presented token."""

    __tablename__ = "credential_verifications"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('VALID', 'INVALID', 'EXPIRED', 'REVOKED', 'UNAVAILABLE')",
            name="ck_cred_verification_outcome",
        ),
        Index("ix_cred_verification_time", "verified_at", "id"),
        Index("ix_cred_verification_user_time", "verifier_user_id", "verified_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Set only when the signature verified, so unauthenticated input cannot probe ids.
    credential_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("admission_credentials.id")
    )
    verifier_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    outcome: Mapped[str] = mapped_column(String(16))
    purpose: Mapped[str] = mapped_column(String(120))
    consent_ref: Mapped[str] = mapped_column(String(64))
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp()
    )
