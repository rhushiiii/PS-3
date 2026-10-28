"""Immutable local validation runs and evidence-linked findings."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_student_validation"
down_revision = "0002_candidate_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_record_batch", "student_record_versions", ["id", "batch_id"]
    )
    op.create_table(
        "validation_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("submission_batches.id"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ruleset_version", sa.String(64), nullable=False),
        sa.Column("ruleset_snapshot_json", postgresql.JSONB(), nullable=False),
        sa.Column("compared_scope_revisions_json", postgresql.JSONB(), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("id", "batch_id", name="uq_validation_run_batch"),
        sa.CheckConstraint(
            "kind IN ('INITIAL', 'REVALIDATION')", name="ck_validation_kind"
        ),
    )
    op.create_index(
        "uq_validation_initial",
        "validation_runs",
        ["batch_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'INITIAL'"),
    )
    op.create_index(
        "ix_validation_batch_time",
        "validation_runs",
        ["batch_id", "evaluated_at", "id"],
    )
    op.create_table(
        "validation_findings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("record_version_id", sa.Uuid(), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_json_redacted", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "batch_id"],
            ["validation_runs.id", "validation_runs.batch_id"],
            name="fk_finding_run_batch",
        ),
        sa.ForeignKeyConstraint(
            ["record_version_id", "batch_id"],
            ["student_record_versions.id", "student_record_versions.batch_id"],
            name="fk_finding_record_batch",
        ),
        sa.UniqueConstraint("run_id", "ordinal", name="uq_finding_ordinal"),
        sa.CheckConstraint("ordinal > 0", name="ck_finding_ordinal"),
        sa.CheckConstraint(
            "severity IN ('ERROR', 'WARNING', 'INFO')", name="ck_finding_severity"
        ),
        sa.CheckConstraint(
            "classification IN ('ACTIVATION_BLOCKING', 'REVIEWABLE')",
            name="ck_finding_classification",
        ),
    )
    op.create_index(
        "ix_finding_record", "validation_findings", ["run_id", "record_version_id"]
    )
    op.execute("""CREATE FUNCTION prevent_validation_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Validation evidence is immutable' USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql""")
    for table in ("validation_runs", "validation_findings"):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION prevent_validation_mutation()"
        )


def downgrade() -> None:
    op.drop_table("validation_findings")
    op.drop_table("validation_runs")
    op.execute("DROP FUNCTION prevent_validation_mutation()")
    op.drop_constraint("uq_record_batch", "student_record_versions", type_="unique")
