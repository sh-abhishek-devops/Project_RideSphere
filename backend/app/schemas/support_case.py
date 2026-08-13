from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SupportCasePriority, SupportCaseStatus, UserRole
from app.schemas.driver import DriverResponse
from app.schemas.payment import PaymentResponse
from app.schemas.ride_request import RideRequestResponse
from app.schemas.rider import RiderResponse
from app.schemas.trip import TripResponse
from app.schemas.vehicle import VehicleResponse


class SupportAgentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool


class SupportCaseCreate(BaseModel):
    ride_request_id: UUID
    issue_summary: str = Field(min_length=3, max_length=255)
    priority: SupportCasePriority = SupportCasePriority.MEDIUM
    assigned_agent_user_id: UUID | None = None


class SupportCaseUpdate(BaseModel):
    assigned_agent_user_id: UUID | None = None
    priority: SupportCasePriority | None = None
    status: SupportCaseStatus | None = None
    resolution_notes: str | None = Field(default=None, max_length=2000)


class SupportCaseResolve(BaseModel):
    resolution_notes: str = Field(min_length=3, max_length=2000)


class SupportCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ride_request_id: UUID
    trip_id: UUID | None
    created_by_user_id: UUID
    assigned_agent_user_id: UUID | None
    issue_summary: str
    priority: SupportCasePriority
    status: SupportCaseStatus
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    created_by_user: SupportAgentSummary
    assigned_agent_user: SupportAgentSummary | None


class SupportInvestigationResponse(BaseModel):
    case: SupportCaseResponse
    rider: RiderResponse
    driver: DriverResponse | None
    vehicle: VehicleResponse | None
    ride_request: RideRequestResponse
    trip: TripResponse | None
    payment: PaymentResponse | None
