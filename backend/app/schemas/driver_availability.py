from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AvailabilityStatus


class DriverAvailabilityCreate(BaseModel):
    driver_id: UUID
    status: AvailabilityStatus
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class DriverAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID
    status: AvailabilityStatus
    latitude: float
    longitude: float
    updated_at: datetime


class DriverSelfAvailabilityUpdate(BaseModel):
    status: AvailabilityStatus
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
