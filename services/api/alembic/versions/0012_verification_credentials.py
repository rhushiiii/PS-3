"""Harden simulated APAAR verification; add signed DEMO admission credentials.

Reuses prevent_intake_history_mutation() from 0010 for append-only/immutable tables.
Existing apaar_verifications rows stay valid: new columns are nullable.
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_verification_credentials"
down_revision = "0011_integrity_decisions"
branch_labels = None
depends_on = None

OLD_STATUSES = (
    "status IN ('SIMULATED_MATCH', 'SIMULATED_MISMATCH', 'PENDING', "
    "'SOURCE_UNAVAILABLE')"
)
NEW_STATUSES = (
    "status IN ('SIMULATED_MATCH', 'SIMULATED_MISMATCH', 'PENDING', "
    "'SOURCE_UNAVAILABLE', 'SOURCE_TIMEOUT')"
)
CREDENTIAL_TABLES = (
    "admission_credentials",
    "credential_revocations",
    "credential_verifications",
)


def upgrade() -> None:
    op.add_column(
        "apaar_verifications",
        sa.Column("provider_request_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "apaar_verifications",
        sa.Column(
            "retry_of_id",
            sa.Uuid(),
            sa.ForeignKey("apaar_verifications.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "apaar_verifications",
        sa.Column("idempotency_key", sa.String(128), nullable=True),
    )
    op.add_column(
        "apaar_verifications",
        sa.Column("request_fingerprint", sa.String(64), nullable=True),
    )
    op.create_index(
        "uq_verification_idempotency",
        "apaar_verifications",
        ["record_version_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.drop_constraint("ck_verification_status", "apaar_verifications")
    op.create_check_constraint(
        "ck_verification_status", "apaar_verifications", NEW_STATUSES
    )

    op.create_table(
        "admission_credentials",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "record_version_id",
            sa.Uuid(),
            sa.ForeignKey("student_record_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            sa.Uuid(),
            sa.ForeignKey("institutions.id"),
            nullable=False,
        ),
        sa.Column("issued_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kid", sa.String(64), nullable=False),
        sa.Column("claims_sha256", sa.String(64), nullable=False),
        sa.Column("source_label", sa.String(16), nullable=False, server_default="DEMO"),
        sa.CheckConstraint("expires_at > issued_at", name="ck_credential_expiry"),
    )
    op.create_index(
        "ix_admission_credentials_record_version_id",
        "admission_credentials",
        ["record_version_id"],
    )
    op.create_index(
        "ix_credential_institution_time",
        "admission_credentials",
        ["institution_id", "issued_at", "id"],
    )
    op.create_table(
        "credential_revocations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "credential_id",
            sa.Uuid(),
            sa.ForeignKey("admission_credentials.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("revoked_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("clock_timestamp()"),
        ),
        sa.CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_revocation_reason"
        ),
    )
    op.create_table(
        "credential_verifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "credential_id",
            sa.Uuid(),
            sa.ForeignKey("admission_credentials.id"),
            nullable=True,
        ),
        sa.Column(
            "verifier_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("purpose", sa.String(120), nullable=False),
        sa.Column("consent_ref", sa.String(64), nullable=False),
        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("clock_timestamp()"),
        ),
        sa.CheckConstraint(
            "outcome IN ('VALID', 'INVALID', 'EXPIRED', 'REVOKED', 'UNAVAILABLE')",
            name="ck_cred_verification_outcome",
        ),
    )
    op.create_index(
        "ix_cred_verification_time", "credential_verifications", ["verified_at", "id"]
    )
    op.create_index(
        "ix_cred_verification_user_time",
        "credential_verifications",
        ["verifier_user_id", "verified_at"],
    )
    for table in CREDENTIAL_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION prevent_intake_history_mutation()"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(
        sa.text("SELECT 1 FROM apaar_verifications WHERE status = 'SOURCE_TIMEOUT'")
    ).first():
        raise RuntimeError(
            "Cannot downgrade: SOURCE_TIMEOUT verification evidence exists and "
            "is immutable"
        )
    for table in reversed(CREDENTIAL_TABLES):
        op.drop_table(table)
    op.drop_constraint("ck_verification_status", "apaar_verifications")
    op.create_check_constraint(
        "ck_verification_status", "apaar_verifications", OLD_STATUSES
    )
    op.drop_index("uq_verification_idempotency", table_name="apaar_verifications")
    for column in (
        "request_fingerprint",
        "idempotency_key",
        "retry_of_id",
        "provider_request_id",
    ):
        op.drop_column("apaar_verifications", column)
