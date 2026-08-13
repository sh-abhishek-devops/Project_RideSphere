from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.services.notification import NotificationService

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=get_settings().celery_task_max_retries,
)
def send_notification_task(self, payload: dict) -> bool:
    recipient_type = payload["recipient_type"]
    recipient_user_id = UUID(payload["recipient_user_id"])
    notification_type = payload["notification_type"]
    context = payload["context"]
    service = NotificationService()

    logger.info("Processing notification task type=%s recipient_type=%s", notification_type, recipient_type)
    if recipient_type == "rider":
        return service.notify_rider(recipient_user_id, notification_type, context)
    if recipient_type == "driver":
        return service.notify_driver(recipient_user_id, notification_type, context)
    raise RuntimeError(f"Unsupported notification recipient type: {recipient_type}")
