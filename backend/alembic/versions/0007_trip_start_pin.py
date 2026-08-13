"""add rider trip start pin

Revision ID: 0007_trip_start_pin
Revises: 0006_support_cases
Create Date: 2026-08-13 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_trip_start_pin"
down_revision: str | None = "0006_support_cases"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("rider_start_pin", sa.String(length=6), nullable=True))
    op.execute("UPDATE trips SET rider_start_pin = '000000' WHERE rider_start_pin IS NULL")
    op.alter_column("trips", "rider_start_pin", nullable=False)


def downgrade() -> None:
    op.drop_column("trips", "rider_start_pin")
