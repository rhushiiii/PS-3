"""Case workflow: priority, severity, due date, resolution reason, new statuses.

Downgrade restores the 0006 status and action sets. It refuses (with a clear
error) when rows already use the new statuses or event actions, because the old
CHECK constraints cannot represent them and case history is append-only.
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_case_workflow"
down_revision = "0007_upload_idempotency"
branch_labels = None
depends_on = None

OLD_STATUSES = ("OPEN", "AWAITING_CORRECTION", "UNDER_REVIEW", "RESOLVED", "CLOSED")
NEW_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "UNDER_REVIEW",
    "AWAITING_CORRECTION",
    "RESPONSE_SUBMITTED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
)
OLD_ACTIONS = (
    "OPENED",
    "COMMENT",
    "REQUEST_CORRECTION",
    "CORRECTION_RECEIVED",
    "ASSIGNED",
    "RESOLVED",
    "CLOSED",
)
NEW_ACTIONS = (
    "OPENED",
    "COMMENT",
    "REQUEST_CORRECTION",
    "CORRECTION_RECEIVED",
    "ASSIGNED",
    "START_REVIEW",
    "RESPONSE_SUBMITTED",
    "UPDATED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
)


def one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def swap_constraint(
    table: str, name: str, column: str, values: tuple[str, ...]
) -> None:
    op.drop_constraint(name, table, type_="check")
    op.create_check_constraint(name, table, one_of(column, values))


def upgrade() -> None:
    op.add_column(
        "review_cases",
        sa.Column("priority", sa.String(16), nullable=False, server_default="MEDIUM"),
    )
    op.add_column(
        "review_cases",
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM"),
    )
    op.add_column(
        "review_cases", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "review_cases", sa.Column("resolution_reason", sa.Text(), nullable=True)
    )
    op.create_check_constraint(
        "ck_case_priority",
        "review_cases",
        one_of("priority", ("LOW", "MEDIUM", "HIGH", "URGENT")),
    )
    op.create_check_constraint(
        "ck_case_severity",
        "review_cases",
        one_of("severity", ("LOW", "MEDIUM", "HIGH", "CRITICAL")),
    )
    op.create_check_constraint(
        "ck_case_resolution_reason",
        "review_cases",
        "resolution_reason IS NULL OR char_length(resolution_reason) <= 2000",
    )
    swap_constraint("review_cases", "ck_case_status", "status", NEW_STATUSES)
    # case_events is append-only (UPDATE/DELETE trigger); changing a CHECK
    # constraint only re-validates existing rows and does not touch them.
    swap_constraint("case_events", "ck_case_event_action", "action", NEW_ACTIONS)


def downgrade() -> None:
    connection = op.get_bind()
    statuses = one_of("status", OLD_STATUSES).replace("status IN", "status NOT IN")
    actions = one_of("action", OLD_ACTIONS).replace("action IN", "action NOT IN")
    blocked = connection.scalar(
        sa.text(
            f"SELECT (SELECT count(*) FROM review_cases WHERE {statuses}) "
            f"+ (SELECT count(*) FROM case_events WHERE {actions})"
        )
    )
    if blocked:
        raise RuntimeError(
            "Cannot downgrade: cases or append-only events already use workflow "
            "statuses/actions that the previous schema cannot represent."
        )
    swap_constraint("case_events", "ck_case_event_action", "action", OLD_ACTIONS)
    swap_constraint("review_cases", "ck_case_status", "status", OLD_STATUSES)
    op.drop_constraint("ck_case_resolution_reason", "review_cases", type_="check")
    op.drop_constraint("ck_case_severity", "review_cases", type_="check")
    op.drop_constraint("ck_case_priority", "review_cases", type_="check")
    op.drop_column("review_cases", "resolution_reason")
    op.drop_column("review_cases", "due_at")
    op.drop_column("review_cases", "severity")
    op.drop_column("review_cases", "priority")
