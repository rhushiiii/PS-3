"""In-app notifications, one row per recipient."""

import sqlalchemy as sa

from alembic import op

revision = "0009_notifications"
down_revision = "0008_case_workflow"
branch_labels = None
depends_on = None

KINDS = (
    "CASE_ASSIGNED",
    "CORRECTION_REQUESTED",
    "RESPONSE_SUBMITTED",
    "CASE_RESOLVED",
    "CASE_REJECTED",
    "CASE_CLOSED",
    "CASE_OVERDUE",
)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "recipient_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "institution_id", sa.Uuid(), sa.ForeignKey("institutions.id"), nullable=True
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column(
            "case_id", sa.Uuid(), sa.ForeignKey("review_cases.id"), nullable=True
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("dedupe_key", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            f"kind IN ({', '.join(repr(kind) for kind in KINDS)})",
            name="ck_notification_kind",
        ),
    )
    op.create_index(
        "ix_notification_recipient_read",
        "notifications",
        ["recipient_user_id", "read_at", "created_at"],
    )
    op.create_index(
        "uq_notification_dedupe",
        "notifications",
        ["recipient_user_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
