"""initial domain models

Revision ID: 0002_initial_domain_models
Revises: 0001_baseline
Create Date: 2026-08-11 00:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_initial_domain_models"
down_revision: str | None = "0001_baseline"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


user_role_enum = sa.Enum(
    "RIDER",
    "DRIVER",
    "SUPPORT_AGENT",
    "PAYMENT_AGENT",
    "OPERATIONS_MANAGER",
    "ADMIN",
    name="user_role",
    native_enum=False,
)

availability_status_enum = sa.Enum(
    "OFFLINE",
    "AVAILABLE",
    "RESERVED",
    "ON_TRIP",
    name="availability_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "riders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_riders_user_id"),
    )
    op.create_index(op.f("ix_riders_user_id"), "riders", ["user_id"], unique=False)

    op.create_table(
        "drivers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_drivers_user_id"),
    )
    op.create_index(op.f("ix_drivers_user_id"), "drivers", ["user_id"], unique=False)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=64), nullable=False),
        sa.Column("license_plate", sa.String(length=32), nullable=False),
        sa.Column("vehicle_type", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_driver_id"), "vehicles", ["driver_id"], unique=False)
    op.create_index(op.f("ix_vehicles_is_active"), "vehicles", ["is_active"], unique=False)
    op.create_index(op.f("ix_vehicles_license_plate"), "vehicles", ["license_plate"], unique=True)
    op.create_index(op.f("ix_vehicles_vehicle_type"), "vehicles", ["vehicle_type"], unique=False)

    op.create_table(
        "driver_availabilities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("status", availability_status_enum, nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_driver_availabilities_driver_id"), "driver_availabilities", ["driver_id"], unique=False)
    op.create_index(op.f("ix_driver_availabilities_status"), "driver_availabilities", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_driver_availabilities_status"), table_name="driver_availabilities")
    op.drop_index(op.f("ix_driver_availabilities_driver_id"), table_name="driver_availabilities")
    op.drop_table("driver_availabilities")

    op.drop_index(op.f("ix_vehicles_vehicle_type"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_license_plate"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_is_active"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_driver_id"), table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index(op.f("ix_drivers_user_id"), table_name="drivers")
    op.drop_table("drivers")

    op.drop_index(op.f("ix_riders_user_id"), table_name="riders")
    op.drop_table("riders")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
