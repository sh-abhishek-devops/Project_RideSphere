import logging
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.services.notification import NotificationService
from app.services.operational_event import OperationalEventService, OperationalEventType

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    def __init__(
        self,
        event_service: OperationalEventService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.event_service = event_service if event_service is not None else OperationalEventService()
        self.notification_service = (
            notification_service if notification_service is not None else NotificationService()
        )

    def dispatch_operational_event(
        self,
        event_type: OperationalEventType,
        *,
        ride_id: UUID | None = None,
        trip_id: UUID | None = None,
        actor_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        payload = {
            "event_type": event_type.value,
            "ride_id": str(ride_id) if ride_id is not None else None,
            "trip_id": str(trip_id) if trip_id is not None else None,
            "actor_id": str(actor_id) if actor_id is not None else None,
            "metadata": metadata or {},
        }
        if self.settings.celery_enabled and self.settings.celery_task_always_eager is False:
            try:
                from app.tasks.operational_event_tasks import process_operational_event_task

                process_operational_event_task.delay(payload)
                return True
            except Exception as exc:
                logger.warning("Failed to queue operational event task, falling back inline: %s", exc)

        return self.event_service.publish(
            event_type,
            ride_id=ride_id,
            trip_id=trip_id,
            actor_id=actor_id,
            metadata=metadata,
        )

    def dispatch_rider_notification(
        self,
        rider_user_id: UUID,
        notification_type: str,
        context: dict[str, Any],
    ) -> bool:
        payload = {
            "recipient_type": "rider",
            "recipient_user_id": str(rider_user_id),
            "notification_type": notification_type,
            "context": context,
        }
        if self.settings.celery_enabled and self.settings.celery_task_always_eager is False:
            try:
                from app.tasks.notification_tasks import send_notification_task

                send_notification_task.delay(payload)
                return True
            except Exception as exc:
                logger.warning("Failed to queue rider notification, falling back inline: %s", exc)

        return self.notification_service.notify_rider(rider_user_id, notification_type, context)

    def dispatch_driver_notification(
        self,
        driver_user_id: UUID,
        notification_type: str,
        context: dict[str, Any],
    ) -> bool:
        payload = {
            "recipient_type": "driver",
            "recipient_user_id": str(driver_user_id),
            "notification_type": notification_type,
            "context": context,
        }
        if self.settings.celery_enabled and self.settings.celery_task_always_eager is False:
            try:
                from app.tasks.notification_tasks import send_notification_task

                send_notification_task.delay(payload)
                return True
            except Exception as exc:
                logger.warning("Failed to queue driver notification, falling back inline: %s", exc)

        return self.notification_service.notify_driver(driver_user_id, notification_type, context)

    def dispatch_payment_processing(self, payment_id: UUID) -> bool:
        if self.settings.celery_enabled and self.settings.celery_task_always_eager is False:
            try:
                from app.tasks.payment_tasks import process_payment_task

                process_payment_task.delay(str(payment_id))
                return True
            except Exception as exc:
                logger.warning("Failed to queue payment processing, falling back inline: %s", exc)

        from app.services.payment import PaymentService

        session = SessionLocal()
        try:
            PaymentService(
                session,
                event_service=self.event_service,
                notification_service=self.notification_service,
            ).process_pending_payment(payment_id)
            return True
        finally:
            session.close()
