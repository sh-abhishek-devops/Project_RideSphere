import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class NotificationService:
    def notify_rider(self, rider_user_id: UUID, notification_type: str, context: dict[str, Any]) -> bool:
        logger.info(
            "Rider notification queued type=%s rider_user_id=%s context=%s",
            notification_type,
            rider_user_id,
            context,
        )
        return True

    def notify_driver(self, driver_user_id: UUID, notification_type: str, context: dict[str, Any]) -> bool:
        logger.info(
            "Driver notification queued type=%s driver_user_id=%s context=%s",
            notification_type,
            driver_user_id,
            context,
        )
        return True
