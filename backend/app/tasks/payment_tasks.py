from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.services.payment import PaymentService

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=get_settings().celery_task_max_retries,
)
def process_payment_task(self, payment_id: str) -> str:
    session = SessionLocal()
    try:
        logger.info("Processing mock payment task payment_id=%s", payment_id)
        payment = PaymentService(session).process_pending_payment(UUID(payment_id))
        return payment.status.value
    finally:
        session.close()
