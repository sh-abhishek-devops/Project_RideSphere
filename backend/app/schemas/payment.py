from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import PaymentStatus


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    rider_id: UUID | None
    amount: float | None
    currency: str | None
    status: PaymentStatus
    payment_reference: str | None
    created_at: datetime
    updated_at: datetime
