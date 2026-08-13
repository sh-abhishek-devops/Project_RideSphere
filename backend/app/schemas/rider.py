from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import NestedUserCreate, UserResponse


class RiderCreate(BaseModel):
    user: NestedUserCreate


class RiderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: UserResponse
