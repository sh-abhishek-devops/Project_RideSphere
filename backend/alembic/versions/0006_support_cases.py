"""add support cases

Revision ID: 0006_support_cases
Revises: 0005_payment_domain
Create Date: 2026-08-11 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_support_cases"
down_revision: str | None = "0005_payment_domain"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ride_request_id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_agent_user_id", sa.Uuid(), nullable=True),
        sa.Column("issue_summary", sa.String(length=255), nullable=False),
        sa.Column(
            "priority",
            sa.Enum(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="support_case_priority",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "ASSIGNED",
                "INVESTIGATING",
                "WAITING_ON_RIDER",
                "WAITING_ON_DRIVER",
                "RESOLVED",
                name="support_case_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("resolution_notes", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_agent_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ride_request_id"], ["ride_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_cases_assigned_agent_user_id"), "support_cases", ["assigned_agent_user_id"], unique=False)
    op.create_index(op.f("ix_support_cases_created_by_user_id"), "support_cases", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_support_cases_priority"), "support_cases", ["priority"], unique=False)
    op.create_index(op.f("ix_support_cases_ride_request_id"), "support_cases", ["ride_request_id"], unique=False)
    op.create_index(op.f("ix_support_cases_status"), "support_cases", ["status"], unique=False)
    op.create_index(op.f("ix_support_cases_trip_id"), "support_cases", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_cases_trip_id"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_status"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_ride_request_id"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_priority"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_created_by_user_id"), table_name="support_cases")
    op.drop_index(op.f("ix_support_cases_assigned_agent_user_id"), table_name="support_cases")
    op.drop_table("support_cases")
