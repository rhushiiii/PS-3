"""Intake governance: rule-change history, declared totals, stored assessments.

All three tables are append-only (UPDATE/DELETE trigger). Values are DEMO only.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010_intake_governance"
down_revision = "0009_notifications"
branch_labels = None
depends_on = None

TABLES = ("intake_rule_changes", "intake_declarations", "intake_assessments")


def clock() -> sa.sql.elements.TextClause:
    # clock_timestamp() (not now()) so rows written in one transaction still order.
    return sa.text("clock_timestamp()")


def upgrade() -> None:
    op.create_table(
        "intake_rule_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "intake_rule_id",
            sa.Uuid(),
            sa.ForeignKey("intake_rules.id"),
            nullable=False,
        ),
        sa.Column("changed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("old_approved_seats", sa.Integer(), nullable=False),
        sa.Column("new_approved_seats", sa.Integer(), nullable=False),
        sa.Column("old_rule_version", sa.String(64), nullable=False),
        sa.Column("new_rule_version", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=clock(),
        ),
        sa.CheckConstraint(
            "old_approved_seats >= 0 AND new_approved_seats >= 0",
            name="ck_rule_change_seats",
        ),
        sa.CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_rule_change_reason"
        ),
    )
    op.create_index(
        "ix_rule_change_rule_time",
        "intake_rule_changes",
        ["intake_rule_id", "created_at"],
    )
    op.create_table(
        "intake_declarations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("programme_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year", sa.String(7), nullable=False),
        sa.Column("declared_total", sa.Integer(), nullable=False),
        sa.Column("source_label", sa.String(32), nullable=False, server_default="DEMO"),
        sa.Column("basis", sa.String(500), nullable=False),
        sa.Column("declared_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=clock(),
        ),
        sa.ForeignKeyConstraint(
            ["programme_id", "institution_id"],
            ["programmes.id", "programmes.institution_id"],
            name="fk_declaration_programme_institution",
        ),
        sa.CheckConstraint("declared_total >= 0", name="ck_declaration_total"),
        sa.CheckConstraint(
            "academic_year ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_declaration_year"
        ),
        sa.CheckConstraint(
            "char_length(basis) BETWEEN 1 AND 500", name="ck_declaration_basis"
        ),
    )
    op.create_index(
        "ix_declaration_scope_time",
        "intake_declarations",
        ["institution_id", "programme_id", "academic_year", "created_at"],
    )
    op.create_table(
        "intake_assessments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("programme_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year", sa.String(7), nullable=False),
        sa.Column("scope_revision", sa.Integer(), nullable=False),
        sa.Column("current_batch_id", sa.Uuid(), nullable=True),
        sa.Column("computed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=clock(),
        ),
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["batch_id", "institution_id", "programme_id", "academic_year"],
            [
                "submission_batches.id",
                "submission_batches.institution_id",
                "submission_batches.programme_id",
                "submission_batches.academic_year",
            ],
            name="fk_assessment_batch_context",
        ),
        sa.CheckConstraint("scope_revision >= 0", name="ck_assessment_revision"),
    )
    op.create_index(
        "ix_assessment_batch_time", "intake_assessments", ["batch_id", "computed_at"]
    )
    op.execute("""CREATE FUNCTION prevent_intake_history_mutation() RETURNS trigger
        AS $$
        BEGIN
            RAISE EXCEPTION 'Intake governance history is append-only'
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql""")
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION prevent_intake_history_mutation()"
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_table(table)
    op.execute("DROP FUNCTION prevent_intake_history_mutation()")
