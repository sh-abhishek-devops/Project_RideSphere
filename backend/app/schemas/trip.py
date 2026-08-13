from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RideType, TripStatus


class TripRideRequestSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    ride_type: RideType


class TripStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    previous_status: TripStatus | None
    new_status: TripStatus
    changed_by: UUID
    timestamp: datetime


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ride_request_id: UUID
    rider_id: UUID
    driver_id: UUID
    vehicle_id: UUID | None
    status: TripStatus
    rider_start_pin: str | None = None
    started_at: datetime | None
    completed_at: datetime | None
    actual_distance: float | None
    actual_duration: int | None
    created_at: datetime
    updated_at: datetime
    ride_request: TripRideRequestSummary
    status_history: list[TripStatusHistoryResponse]


class TripCompletionRequest(BaseModel):
    actual_distance: float = Field(gt=0)
    actual_duration: int = Field(gt=0)


class TripStartRequest(BaseModel):
    rider_start_pin: str = Field(pattern=r"^\d{6}$")
