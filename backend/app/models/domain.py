import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.models.enums import (
    AvailabilityStatus,
    PaymentStatus,
    RideRequestStatus,
    RideType,
    SupportCasePriority,
    SupportCaseStatus,
    TripStatus,
    UserRole,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(32), index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, validate_strings=True),
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    rider_profile: Mapped["Rider | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    driver_profile: Mapped["Driver | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    created_support_cases: Mapped[list["SupportCase"]] = relationship(
        back_populates="created_by_user",
        cascade="all, delete-orphan",
        foreign_keys="SupportCase.created_by_user_id",
    )
    assigned_support_cases: Mapped[list["SupportCase"]] = relationship(
        back_populates="assigned_agent_user",
        foreign_keys="SupportCase.assigned_agent_user_id",
    )


class Rider(Base):
    __tablename__ = "riders"
    __table_args__ = (UniqueConstraint("user_id", name="uq_riders_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="rider_profile")
    ride_requests: Mapped[list["RideRequest"]] = relationship(
        back_populates="rider", cascade="all, delete-orphan"
    )
    trips: Mapped[list["Trip"]] = relationship(back_populates="rider")
    payments: Mapped[list["Payment"]] = relationship(back_populates="rider")


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (UniqueConstraint("user_id", name="uq_drivers_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="driver_profile")
    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="driver", cascade="all, delete-orphan"
    )
    availability_records: Mapped[list["DriverAvailability"]] = relationship(
        back_populates="driver", cascade="all, delete-orphan"
    )
    assigned_rides: Mapped[list["RideRequest"]] = relationship(back_populates="driver")
    trips: Mapped[list["Trip"]] = relationship(back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(String(64))
    license_plate: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    driver: Mapped[Driver] = relationship(back_populates="vehicles")
    trips: Mapped[list["Trip"]] = relationship(back_populates="vehicle")


class DriverAvailability(Base):
    __tablename__ = "driver_availabilities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(
            AvailabilityStatus,
            name="availability_status",
            native_enum=False,
            validate_strings=True,
        ),
        index=True,
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    driver: Mapped[Driver] = relationship(back_populates="availability_records")


class RideRequest(Base):
    __tablename__ = "ride_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pickup_address: Mapped[str] = mapped_column(String(255))
    pickup_latitude: Mapped[float] = mapped_column(Float)
    pickup_longitude: Mapped[float] = mapped_column(Float)
    destination_address: Mapped[str] = mapped_column(String(255))
    destination_latitude: Mapped[float] = mapped_column(Float)
    destination_longitude: Mapped[float] = mapped_column(Float)
    ride_type: Mapped[RideType] = mapped_column(
        Enum(RideType, name="ride_type", native_enum=False, validate_strings=True),
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    status: Mapped[RideRequestStatus] = mapped_column(
        Enum(
            RideRequestStatus,
            name="ride_request_status",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    estimated_distance: Mapped[float] = mapped_column(Float)
    estimated_duration: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    rider: Mapped[Rider] = relationship(back_populates="ride_requests")
    driver: Mapped[Driver | None] = relationship(back_populates="assigned_rides")
    trip: Mapped["Trip | None"] = relationship(back_populates="ride_request", uselist=False)
    support_cases: Mapped[list["SupportCase"]] = relationship(
        back_populates="ride_request",
        cascade="all, delete-orphan",
    )


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (UniqueConstraint("ride_request_id", name="uq_trips_ride_request_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ride_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ride_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status", native_enum=False, validate_strings=True),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    ride_request: Mapped[RideRequest] = relationship(back_populates="trip")
    rider: Mapped[Rider] = relationship(back_populates="trips")
    driver: Mapped[Driver] = relationship(back_populates="trips")
    vehicle: Mapped[Vehicle | None] = relationship(back_populates="trips")
    status_history: Mapped[list["TripStatusHistory"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", order_by="TripStatusHistory.timestamp"
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        uselist=False,
    )
    support_cases: Mapped[list["SupportCase"]] = relationship(back_populates="trip")


class TripStatusHistory(Base):
    __tablename__ = "trip_status_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_status: Mapped[TripStatus | None] = mapped_column(
        Enum(TripStatus, name="trip_status", native_enum=False, validate_strings=True),
        nullable=True,
    )
    new_status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status", native_enum=False, validate_strings=True),
        nullable=False,
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    trip: Mapped[Trip] = relationship(back_populates="status_history")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("trip_id", name="uq_payments_trip_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", native_enum=False, validate_strings=True),
        nullable=False,
        index=True,
    )
    payment_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trip: Mapped[Trip] = relationship(back_populates="payment")
    rider: Mapped[Rider] = relationship(back_populates="payments")


class SupportCase(Base):
    __tablename__ = "support_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ride_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ride_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_agent_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    issue_summary: Mapped[str] = mapped_column(String(255))
    priority: Mapped[SupportCasePriority] = mapped_column(
        Enum(
            SupportCasePriority,
            name="support_case_priority",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
        default=SupportCasePriority.MEDIUM,
    )
    status: Mapped[SupportCaseStatus] = mapped_column(
        Enum(
            SupportCaseStatus,
            name="support_case_status",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
        default=SupportCaseStatus.OPEN,
    )
    resolution_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ride_request: Mapped[RideRequest] = relationship(back_populates="support_cases")
    trip: Mapped[Trip | None] = relationship(back_populates="support_cases")
    created_by_user: Mapped[User] = relationship(
        back_populates="created_support_cases",
        foreign_keys=[created_by_user_id],
    )
    assigned_agent_user: Mapped[User | None] = relationship(
        back_populates="assigned_support_cases",
        foreign_keys=[assigned_agent_user_id],
    )
