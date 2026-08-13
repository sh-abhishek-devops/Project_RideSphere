"""trip domain

Revision ID: 0004_trip_domain
Revises: 0003_ride_request_module
Create Date: 2026-08-11 02:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_trip_domain"
down_revision: str | None = "0003_ride_request_module"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


trip_status_enum = sa.Enum(
    "DRIVER_ASSIGNED",
    "DRIVER_EN_ROUTE",
    "DRIVER_ARRIVED",
    "TRIP_STARTED",
    "TRIP_COMPLETED",
    "CANCELLED",
    name="trip_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ride_request_id", sa.Uuid(), nullable=False),
        sa.Column("rider_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("status", trip_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_distance", sa.Float(), nullable=True),
        sa.Column("actual_duration", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ride_request_id"], ["ride_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ride_request_id", name="uq_trips_ride_request_id"),
    )
    op.create_index(op.f("ix_trips_driver_id"), "trips", ["driver_id"], unique=False)
    op.create_index(op.f("ix_trips_ride_request_id"), "trips", ["ride_request_id"], unique=False)
    op.create_index(op.f("ix_trips_rider_id"), "trips", ["rider_id"], unique=False)
    op.create_index(op.f("ix_trips_status"), "trips", ["status"], unique=False)
    op.create_index(op.f("ix_trips_vehicle_id"), "trips", ["vehicle_id"], unique=False)

    op.create_table(
        "trip_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", trip_status_enum, nullable=True),
        sa.Column("new_status", trip_status_enum, nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_status_history_changed_by"), "trip_status_history", ["changed_by"], unique=False)
    op.create_index(op.f("ix_trip_status_history_timestamp"), "trip_status_history", ["timestamp"], unique=False)
    op.create_index(op.f("ix_trip_status_history_trip_id"), "trip_status_history", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_status_history_trip_id"), table_name="trip_status_history")
    op.drop_index(op.f("ix_trip_status_history_timestamp"), table_name="trip_status_history")
    op.drop_index(op.f("ix_trip_status_history_changed_by"), table_name="trip_status_history")
    op.drop_table("trip_status_history")

    op.drop_index(op.f("ix_trips_vehicle_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_status"), table_name="trips")
    op.drop_index(op.f("ix_trips_rider_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_ride_request_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_driver_id"), table_name="trips")
    op.drop_table("trips")
