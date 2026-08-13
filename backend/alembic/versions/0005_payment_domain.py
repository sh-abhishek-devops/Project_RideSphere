"""add payment domain

Revision ID: 0005_payment_domain
Revises: 0004_trip_domain
Create Date: 2026-08-11 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_payment_domain"
down_revision: str | None = "0004_trip_domain"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("rider_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "SUCCESS",
                "FAILED",
                "REFUNDED",
                name="payment_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("payment_reference", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_reference"),
        sa.UniqueConstraint("trip_id", name="uq_payments_trip_id"),
    )
    op.create_index(op.f("ix_payments_payment_reference"), "payments", ["payment_reference"], unique=True)
    op.create_index(op.f("ix_payments_rider_id"), "payments", ["rider_id"], unique=False)
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)
    op.create_index(op.f("ix_payments_trip_id"), "payments", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_trip_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_rider_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_payment_reference"), table_name="payments")
    op.drop_table("payments")
