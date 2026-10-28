"""Officer cases: manually-opened, append-only evidence links and timeline."""

import sqlalchemy as sa

from alembic import op

revision = "0006_officer_cases"
down_revision = "0005_apaar_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "institution_id",
            sa.Uuid(),
            sa.ForeignKey("institutions.id"),
            nullable=False,
        ),
        sa.Column("opened_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('OPEN', 'AWAITING_CORRECTION', 'UNDER_REVIEW', 'RESOLVED', "
            "'CLOSED')",
            name="ck_case_status",
        ),
        sa.CheckConstraint(
            "category IN ('POTENTIAL_DUPLICATE', 'APAAR_MISMATCH', "
            "'INTAKE_DISCREPANCY', 'OTHER')",
            name="ck_case_category",
        ),
    )
    op.create_index(
        "ix_case_institution_status", "review_cases", ["institution_id", "status"]
    )
    op.create_table(
        "case_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "case_id", sa.Uuid(), sa.ForeignKey("review_cases.id"), nullable=False
        ),
        sa.Column("record_version_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("linked_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "linked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_case_record_batch",
        ),
        sa.UniqueConstraint("case_id", "record_version_id", name="uq_case_record"),
    )
    op.create_table(
        "case_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "ordinal", sa.BigInteger(), sa.Identity(), nullable=False, unique=True
        ),
        sa.Column(
            "case_id", sa.Uuid(), sa.ForeignKey("review_cases.id"), nullable=False
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("linked_batch_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "action IN ('OPENED', 'COMMENT', 'REQUEST_CORRECTION', "
            "'CORRECTION_RECEIVED', 'ASSIGNED', 'RESOLVED', 'CLOSED')",
            name="ck_case_event_action",
        ),
    )
    op.create_index("ix_case_event_case_ordinal", "case_events", ["case_id", "ordinal"])
    op.execute("""CREATE FUNCTION prevent_case_history_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Case history is immutable' USING ERRCODE='55000';
        END;
        $$ LANGUAGE plpgsql""")
    for table in ("case_records", "case_events"):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION prevent_case_history_mutation()"
        )


def downgrade() -> None:
    for table in ("case_records", "case_events"):
        op.execute(f"DROP TRIGGER {table}_immutable ON {table}")
    op.execute("DROP FUNCTION prevent_case_history_mutation()")
    op.drop_table("case_events")
    op.drop_table("case_records")
    op.drop_table("review_cases")
