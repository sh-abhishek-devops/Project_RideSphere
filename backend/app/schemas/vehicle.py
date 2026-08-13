from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    driver_id: UUID
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)
    color: str = Field(min_length=1, max_length=64)
    license_plate: str = Field(min_length=1, max_length=32)
    vehicle_type: str = Field(min_length=1, max_length=64)
    is_active: bool = True


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    vehicle_type: str
    is_active: bool
