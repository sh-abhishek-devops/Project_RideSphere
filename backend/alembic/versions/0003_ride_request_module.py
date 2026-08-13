"""ride request module

Revision ID: 0003_ride_request_module
Revises: 0002_initial_domain_models
Create Date: 2026-08-11 01:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_ride_request_module"
down_revision: str | None = "0002_initial_domain_models"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


ride_type_enum = sa.Enum("STANDARD", "XL", "PREMIUM", name="ride_type", native_enum=False)
ride_request_status_enum = sa.Enum(
    "REQUESTED",
    "SEARCHING_DRIVER",
    "DRIVER_ASSIGNED",
    "CANCELLED",
    name="ride_request_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "ride_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rider_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=True),
        sa.Column("pickup_address", sa.String(length=255), nullable=False),
        sa.Column("pickup_latitude", sa.Float(), nullable=False),
        sa.Column("pickup_longitude", sa.Float(), nullable=False),
        sa.Column("destination_address", sa.String(length=255), nullable=False),
        sa.Column("destination_latitude", sa.Float(), nullable=False),
        sa.Column("destination_longitude", sa.Float(), nullable=False),
        sa.Column("ride_type", ride_type_enum, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status", ride_request_status_enum, nullable=False),
        sa.Column("estimated_distance", sa.Float(), nullable=False),
        sa.Column("estimated_duration", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ride_requests_driver_id"), "ride_requests", ["driver_id"], unique=False)
    op.create_index(op.f("ix_ride_requests_rider_id"), "ride_requests", ["rider_id"], unique=False)
    op.create_index(op.f("ix_ride_requests_requested_at"), "ride_requests", ["requested_at"], unique=False)
    op.create_index(op.f("ix_ride_requests_ride_type"), "ride_requests", ["ride_type"], unique=False)
    op.create_index(op.f("ix_ride_requests_status"), "ride_requests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ride_requests_driver_id"), table_name="ride_requests")
    op.drop_index(op.f("ix_ride_requests_status"), table_name="ride_requests")
    op.drop_index(op.f("ix_ride_requests_ride_type"), table_name="ride_requests")
    op.drop_index(op.f("ix_ride_requests_requested_at"), table_name="ride_requests")
    op.drop_index(op.f("ix_ride_requests_rider_id"), table_name="ride_requests")
    op.drop_table("ride_requests")
