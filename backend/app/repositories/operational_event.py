from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from pymongo.collection import Collection

from app.database.mongo import get_operational_events_collection


@dataclass(slots=True)
class OperationalEventRecord:
    event_type: str
    ride_id: UUID | None
    trip_id: UUID | None
    actor_id: UUID | None
    metadata: dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_document(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "ride_id": str(self.ride_id) if self.ride_id is not None else None,
            "trip_id": str(self.trip_id) if self.trip_id is not None else None,
            "actor_id": str(self.actor_id) if self.actor_id is not None else None,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class OperationalEventRepository(Protocol):
    def save(self, event: OperationalEventRecord) -> None: ...


class MongoOperationalEventRepository:
    def __init__(self, collection: Collection | None = None) -> None:
        self.collection = collection if collection is not None else get_operational_events_collection()

    def save(self, event: OperationalEventRecord) -> None:
        if self.collection is None:
            return
        self.collection.insert_one(event.to_document())
