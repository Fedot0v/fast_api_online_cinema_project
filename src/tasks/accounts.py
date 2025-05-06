from datetime import datetime, timezone
import logging
import asyncio

from celery import shared_task
from sqlalchemy import delete

from src.config.settings import get_settings
from src.database import get_db
from src.database.models.accounts import RefreshTokenModel
from src.services.emails import EmailSenderService

logger = logging.getLogger(__name__)


@shared_task
async def clean_expired_tokens():
    """Periodically clean expired refresh tokens from the database."""
    logger.info("Starting cleanup of expired refresh tokens")
    try:
        async with get_db() as db:
            async with db.begin():
                stmt = delete(RefreshTokenModel).where(
                    RefreshTokenModel.expires_at < datetime.now(timezone.utc)
                )
                result = await db.execute(stmt)
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} expired tokens")
    except asyncio.CancelledError:
        logger.warning("Token cleanup task was cancelled")
        raise
    except Exception as e:
        logger.error(
            f"Error during cleanup of expired refresh tokens: {str(e)}",
            exc_info=True
        )
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
async def send_email_task(
        email_type: str,
        recipient: str,
        link: str
):
    """Args:
        email_type (str): Type of email (
        'activation',
        'activation_complete',
        'password_reset',
        'password_reset_complete'
        ).
        recipient (str): Email address of the recipient.
        link (str): Activation or reset link.
    """

    logger.info(f"Queuing {email_type} email for {recipient}")
    try:
        settings = get_settings()
        email_service = EmailSenderService(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            email=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            template_dir=settings.TEMPLATE_DIR,
            activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
            activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
            password_email_template_name=settings.PASSWORD_EMAIL_TEMPLATE_NAME,
            password_complete_email_template_name=settings.PASSWORD_COMPLETE_EMAIL_TEMPLATE_NAME,
        )

        try:
            if email_type == "activation":
                await email_service.send_activation_email(recipient, link)
            elif email_type == "activation_complete":
                await email_service.send_activation_complete_email(recipient, link)
            elif email_type == "password_reset":
                await email_service.send_password_reset_email(recipient, link)
            elif email_type == "password_reset_complete":
                await email_service.send_password_reset_complete_email(recipient, link)
            else:
                raise ValueError(f"Unknown email type: {email_type}")
        except asyncio.CancelledError:
            logger.warning(f"Email sending task was cancelled for {recipient}")
            raise send_email_task.retry(exc=None, countdown=60, max_retries=3)

        logger.info(f"{email_type.capitalize()} email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send {email_type} email to {recipient}: {str(e)}", exc_info=True)
        raise send_email_task.retry(exc=e, countdown=60, max_retries=3)
