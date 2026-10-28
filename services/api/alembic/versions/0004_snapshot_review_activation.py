"""Immutable review receipts and one-time activation provenance."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_snapshot_review_activation"
down_revision = "0003_student_validation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submission_batches",
        sa.Column("activation_review_id", sa.Uuid(), nullable=True),
    )
    op.create_table(
        "submission_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=False),
        sa.Column("validation_run_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expected_scope_revision", sa.Integer(), nullable=False),
        sa.Column("expected_current_batch_id", sa.Uuid(), nullable=True),
        sa.Column("review_policy_version", sa.String(64), nullable=False),
        sa.Column("review_snapshot_json", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("id", "batch_id", name="uq_review_batch"),
        sa.ForeignKeyConstraint(
            ["batch_id", "scope_id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_review_batch_scope",
        ),
        sa.ForeignKeyConstraint(
            ["validation_run_id", "batch_id"],
            ["validation_runs.id", "validation_runs.batch_id"],
            name="fk_review_run_batch",
        ),
        sa.ForeignKeyConstraint(
            ["expected_current_batch_id", "scope_id"],
            ["submission_batches.id", "submission_batches.scope_id"],
            name="fk_review_current_scope",
        ),
        sa.CheckConstraint("expected_scope_revision >= 0", name="ck_review_revision"),
    )
    op.create_index(
        "ix_review_batch_time", "submission_reviews", ["batch_id", "created_at", "id"]
    )
    op.create_foreign_key(
        "fk_batch_activation_review",
        "submission_batches",
        "submission_reviews",
        ["activation_review_id", "id"],
        ["id", "batch_id"],
    )
    op.create_check_constraint(
        "ck_batch_activation_pair",
        "submission_batches",
        "(activated_at IS NULL) = (activation_review_id IS NULL)",
    )
    op.execute("""CREATE FUNCTION protect_submission_activation() RETURNS trigger AS $$
        BEGIN
            IF TG_TABLE_NAME = 'submission_reviews' THEN
                RAISE EXCEPTION 'Review information is immutable' USING ERRCODE='55000';
            END IF;
            IF OLD.activated_at IS NOT NULL AND
                (NEW.activated_at IS DISTINCT FROM OLD.activated_at OR
                 NEW.activation_review_id IS DISTINCT FROM
                    OLD.activation_review_id) THEN
                RAISE EXCEPTION 'Activation provenance is immutable'
                    USING ERRCODE='55000';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql""")
    op.execute("""CREATE TRIGGER submission_reviews_immutable
        BEFORE UPDATE OR DELETE ON submission_reviews FOR EACH ROW
        EXECUTE FUNCTION protect_submission_activation()""")
    op.execute("""CREATE TRIGGER batch_activation_immutable
        BEFORE UPDATE ON submission_batches FOR EACH ROW
        EXECUTE FUNCTION protect_submission_activation()""")


def downgrade() -> None:
    op.execute("DROP TRIGGER batch_activation_immutable ON submission_batches")
    op.drop_constraint(
        "fk_batch_activation_review", "submission_batches", type_="foreignkey"
    )
    op.drop_constraint("ck_batch_activation_pair", "submission_batches", type_="check")
    op.drop_table("submission_reviews")
    op.drop_column("submission_batches", "activation_review_id")
    op.execute("DROP FUNCTION protect_submission_activation()")
