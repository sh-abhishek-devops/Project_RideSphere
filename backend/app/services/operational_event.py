import logging
from enum import StrEnum
from typing import Any
from uuid import UUID

from pymongo.errors import PyMongoError

from app.repositories.operational_event import (
    MongoOperationalEventRepository,
    OperationalEventRecord,
    OperationalEventRepository,
)

logger = logging.getLogger(__name__)


class OperationalEventType(StrEnum):
    RIDE_REQUESTED = "RIDE_REQUESTED"
    DRIVER_SEARCH_STARTED = "DRIVER_SEARCH_STARTED"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_EN_ROUTE = "DRIVER_EN_ROUTE"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    TRIP_STARTED = "TRIP_STARTED"
    TRIP_COMPLETED = "TRIP_COMPLETED"
    RIDE_CANCELLED = "RIDE_CANCELLED"
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_CREATED = "REFUND_CREATED"
    SUPPORT_CASE_CREATED = "SUPPORT_CASE_CREATED"


class OperationalEventService:
    def __init__(
        self,
        repository: OperationalEventRepository | None = None,
    ) -> None:
        self.repository = repository if repository is not None else MongoOperationalEventRepository()

    def publish(
        self,
        event_type: OperationalEventType,
        *,
        ride_id: UUID | None = None,
        trip_id: UUID | None = None,
        actor_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        event = OperationalEventRecord(
            event_type=event_type.value,
            ride_id=ride_id,
            trip_id=trip_id,
            actor_id=actor_id,
            metadata=self._sanitize_metadata(metadata or {}),
        )

        try:
            self.repository.save(event)
            return True
        except (PyMongoError, OSError, RuntimeError, ValueError) as exc:
            logger.warning("Operational event logging failed for %s: %s", event_type.value, exc)
            return False

    @classmethod
    def _sanitize_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}

        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, UUID):
                sanitized[key] = str(value)
            elif isinstance(value, dict):
                sanitized[key] = cls._sanitize_metadata(value)
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)

        return sanitized
