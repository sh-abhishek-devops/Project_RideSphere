from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.services.operational_event import OperationalEventService, OperationalEventType

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=get_settings().celery_task_max_retries,
)
def process_operational_event_task(self, payload: dict) -> bool:
    logger.info("Processing operational event task type=%s", payload["event_type"])
    published = OperationalEventService().publish(
        OperationalEventType(payload["event_type"]),
        ride_id=UUID(payload["ride_id"]) if payload.get("ride_id") else None,
        trip_id=UUID(payload["trip_id"]) if payload.get("trip_id") else None,
        actor_id=UUID(payload["actor_id"]) if payload.get("actor_id") else None,
        metadata=payload.get("metadata"),
    )
    if published is False:
        raise RuntimeError(f"Operational event task failed for {payload['event_type']}")
    return True
