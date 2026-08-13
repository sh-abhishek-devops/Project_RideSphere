from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RideRequestStatus, RideType
from app.schemas.trip import TripResponse


class RideRequestCreate(BaseModel):
    pickup_address: str = Field(min_length=3, max_length=255)
    pickup_latitude: float = Field(ge=-90, le=90)
    pickup_longitude: float = Field(ge=-180, le=180)
    destination_address: str = Field(min_length=3, max_length=255)
    destination_latitude: float = Field(ge=-90, le=90)
    destination_longitude: float = Field(ge=-180, le=180)
    ride_type: RideType
    estimated_distance: float = Field(gt=0)
    estimated_duration: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_locations_are_different(self):
        same_address = self.pickup_address.strip().lower() == self.destination_address.strip().lower()
        same_coordinates = (
            self.pickup_latitude == self.destination_latitude
            and self.pickup_longitude == self.destination_longitude
        )

        if same_address or same_coordinates:
            raise ValueError("Pickup and destination cannot be identical.")
        return self


class RideRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rider_id: UUID
    driver_id: UUID | None
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    ride_type: RideType
    requested_at: datetime
    status: RideRequestStatus
    estimated_distance: float
    estimated_duration: int
    rider_start_pin: str | None = None
    created_at: datetime
    updated_at: datetime
    trip: TripResponse | None = None
