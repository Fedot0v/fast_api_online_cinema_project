import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.database import get_db
from src.config.dependencies import get_jwt_auth_manager, get_settings
from src.repositories.accounts.accounts import (
    UserRepository,
    ActivationTokenRepository,
    RefreshTokenRepository
)
from src.repositories.accounts.profiles import ProfileRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.services.auth.activation_token_service import ActivationTokenService
from src.services.auth.admin_service import AdminService
from src.services.auth.password_reset_token_service import PasswordResetTokenService
from src.services.auth.registration_service import RegistrationService
from src.services.auth.user_auth_service import UserAuthService
from src.services.auth.user_service import UserService
from src.services.emails import EmailSenderService
from src.services.profiles.profile_service import ProfileService
from src.services.validation.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    logger.info("Creating UserRepository instance")
    return UserRepository(db)


def get_email_service(settings: Settings = Depends(get_settings)) -> EmailSenderService:
    logger.info("Creating EmailSenderService instance")
    try:
        email_service = EmailSenderService(
            hostname=settings.EMAIL_HOSTNAME,
            port=settings.EMAIL_PORT,
            email=settings.EMAIL_ADDRESS,
            password=settings.EMAIL_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            template_dir=settings.EMAIL_TEMPLATE_DIR,
            activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE,
            activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE,
            password_email_template_name=settings.PASSWORD_EMAIL_TEMPLATE,
            password_complete_email_template_name=settings.PASSWORD_COMPLETE_EMAIL_TEMPLATE,
        )
        logger.info("EmailSenderService created successfully")
        return email_service
    except Exception as e:
        logger.error(f"Failed to create EmailSenderService: {e}", exc_info=True)
        raise

def get_token_repository(
        db: AsyncSession = Depends(get_db)
) -> ActivationTokenRepository:
    logger.info("Creating ActivationTokenRepository instance")
    return ActivationTokenRepository(db)

def user_validation_service(
        user_rep: UserRepository = Depends(get_user_repository)
) -> UserValidationService:
    logger.info("Creating UserValidationService instance")
    return UserValidationService(user_rep)

def get_refresh_token_repository(
        db: AsyncSession = Depends(get_db)
) -> RefreshTokenRepository:
    logger.info("Creating RefreshTokenRepository instance")
    return RefreshTokenRepository(db)

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    logger.info("Creating UserRepository instance")
    return UserRepository(db)

def get_user_auth_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    user_validation_service: UserValidationService = Depends(user_validation_service),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_token_repository: RefreshTokenRepository = Depends(get_refresh_token_repository)
) -> UserAuthService:
    logger.info("Creating UserAuthService instance")
    return UserAuthService(
        db=db,
        jwt_manager=jwt_manager,
        user_repository=user_repository,
        user_validation_service=user_validation_service,
        refresh_token_rep=refresh_token_repository
    )

def get_activation_token_service(
        db: AsyncSession = Depends(get_db),
        email_sender_service: EmailSenderService = Depends(get_email_service),
        token_repository: ActivationTokenRepository = Depends(get_token_repository),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> ActivationTokenService:
    logger.info("Creating ActivationTokenService instance")
    return ActivationTokenService(
        db=db,
        email_sender_service=email_sender_service,
        token_repository=token_repository,
        jwt_manager=jwt_manager
    )

def get_password_reset_token_service(
        db: AsyncSession = Depends(get_db),
        email_sender_service: EmailSenderService = Depends(get_email_service)
) -> PasswordResetTokenService:
    logger.info("Creating PasswordResetTokenService instance")
    return PasswordResetTokenService(db, email_sender_service)

def get_register_service(
        db: AsyncSession = Depends(get_db),
        user_repository: UserRepository = Depends(get_user_repository),
        email_sender_service: EmailSenderService = Depends(get_email_service),
        user_validation_service: UserValidationService = Depends(user_validation_service),
        activation_token_service: ActivationTokenService = Depends(get_activation_token_service),
) -> RegistrationService:
    logger.info("Creating RegistrationService instance")
    return RegistrationService(
        db=db,
        user_repository=user_repository,
        email_sender_service=email_sender_service,
        user_validation_service=user_validation_service,
        activation_token_service=activation_token_service,
    )

def get_user_service(
        db: AsyncSession = Depends(get_db),
        user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(db, user_repository)

def get_admin_service(
        db: AsyncSession = Depends(get_db),
        user_repository: UserRepository = Depends(get_user_repository)
) -> AdminService:
    return AdminService(db, user_repository)

def get_profile_repository(
        db: AsyncSession = Depends(get_db)
) -> ProfileRepository:
    return ProfileRepository(db)

def get_profile_service(
        profile_repository: ProfileRepository = Depends(get_profile_repository)
) -> ProfileService:
    return ProfileService(profile_repository)