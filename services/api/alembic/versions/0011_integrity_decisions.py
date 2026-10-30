"""Officer decisions on integrity review prompts (append-only).

Reuses prevent_intake_history_mutation() from 0010 for the immutability trigger.
"""

import sqlalchemy as sa

from alembic import op

revision = "0011_integrity_decisions"
down_revision = "0010_intake_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrity_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "institution_id",
            sa.Uuid(),
            sa.ForeignKey("institutions.id"),
            nullable=False,
        ),
        sa.Column("signal_key", sa.Text(), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("clock_timestamp()"),
        ),
        sa.CheckConstraint(
            "decision IN ('FALSE_POSITIVE', 'CONFIRMED_CONCERN', 'NEEDS_FOLLOW_UP')",
            name="ck_integrity_decision",
        ),
        sa.CheckConstraint(
            "char_length(reason) BETWEEN 3 AND 500", name="ck_integrity_reason"
        ),
        sa.CheckConstraint(
            "char_length(signal_key) BETWEEN 1 AND 300", name="ck_integrity_key"
        ),
    )
    op.create_index(
        "ix_integrity_decision_key_time",
        "integrity_decisions",
        ["institution_id", "signal_key", "created_at"],
    )
    op.execute(
        "CREATE TRIGGER integrity_decisions_immutable BEFORE UPDATE OR DELETE "
        "ON integrity_decisions FOR EACH ROW "
        "EXECUTE FUNCTION prevent_intake_history_mutation()"
    )


def downgrade() -> None:
    op.drop_table("integrity_decisions")
