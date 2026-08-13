from pydantic import BaseModel

from app.schemas.driver import DriverResponse
from app.schemas.rider import RiderResponse
from app.schemas.user import CurrentUserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RiderRegistrationResponse(BaseModel):
    rider: RiderResponse


class DriverRegistrationResponse(BaseModel):
    driver: DriverResponse


class CurrentUserEnvelope(BaseModel):
    user: CurrentUserResponse
