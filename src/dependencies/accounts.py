from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.database import get_db
from src.config.dependencies import get_jwt_auth_manager, get_settings
from src.security.interfaces import JWTAuthManagerInterface
from src.services.accounts import UserAccountService, ActivationTokenService, PasswordResetTokenService
from src.services.emails import EmailSenderService


def get_email_service(
    settings: Settings = Depends(get_settings)
) -> EmailSenderService:
    return EmailSenderService(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME
    )


def get_user_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    email_sender_service: EmailSenderService = Depends(get_email_service)
) -> UserAccountService:
    return UserAccountService(db, jwt_manager, email_sender_service)


def get_activation_token_service(
        db: AsyncSession = Depends(get_db)
) -> ActivationTokenService:
    return ActivationTokenService(db)


def get_password_reset_token_service(
        db: AsyncSession = Depends(get_db)
) -> PasswordResetTokenService:
    return PasswordResetTokenService(db)
