"""Simulated APAAR identity verification records, append-only evidence."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005_apaar_verification"
down_revision = "0004_snapshot_review_activation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apaar_verifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("record_version_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("adapter_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("evidence_json_redacted", postgresql.JSONB(), nullable=False),
        sa.Column("consent_ref", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(120), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_verification_record_batch",
        ),
        sa.CheckConstraint(
            "status IN ('SIMULATED_MATCH', 'SIMULATED_MISMATCH', 'PENDING', "
            "'SOURCE_UNAVAILABLE')",
            name="ck_verification_status",
        ),
    )
    op.create_index(
        "ix_verification_record_time",
        "apaar_verifications",
        ["record_version_id", "requested_at", "id"],
    )
    op.execute("""CREATE FUNCTION prevent_verification_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Verification evidence is immutable' USING ERRCODE='55000';
        END;
        $$ LANGUAGE plpgsql""")
    op.execute(
        "CREATE TRIGGER apaar_verifications_immutable BEFORE UPDATE OR DELETE "
        "ON apaar_verifications FOR EACH ROW "
        "EXECUTE FUNCTION prevent_verification_mutation()"
    )


def downgrade() -> None:
    op.drop_table("apaar_verifications")
    op.execute("DROP FUNCTION prevent_verification_mutation()")
