"""Optional upload idempotency keys, scoped per institution."""

import sqlalchemy as sa

from alembic import op

revision = "0007_upload_idempotency"
down_revision = "0006_officer_cases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submission_batches",
        sa.Column("idempotency_key", sa.String(128), nullable=True),
    )
    op.add_column(
        "submission_batches",
        sa.Column("idempotency_fingerprint", sa.String(64), nullable=True),
    )
    op.create_index(
        "uq_batch_idempotency",
        "submission_batches",
        ["institution_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_batch_idempotency", table_name="submission_batches")
    op.drop_column("submission_batches", "idempotency_fingerprint")
    op.drop_column("submission_batches", "idempotency_key")
