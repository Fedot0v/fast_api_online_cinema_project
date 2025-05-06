import logging
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    BASE_URL: str = "http://localhost:8000"
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "movies.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/cinema_db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")
    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH")
    JWT_SIGNING_ALGORITHM: str = "HS256"
    EMAIL_HOSTNAME: str = os.getenv("EMAIL_HOSTNAME")
    EMAIL_PORT: int = 587
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
    EMAIL_USE_TLS: bool = False
    EMAIL_TEMPLATE_DIR: str = "templates/email"
    ACTIVATION_EMAIL_TEMPLATE: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE: str = "activation_complete.html"
    PASSWORD_EMAIL_TEMPLATE: str = "password_reset_request.html"
    PASSWORD_COMPLETE_EMAIL_TEMPLATE: str = "password_reset_complete.html"
    APP_BASE_URL: str = "http://localhost:8000"
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_settings(self):
        missing_fields = []
        for field in ["SECRET_KEY_ACCESS", "SECRET_KEY_REFRESH", "EMAIL_HOSTNAME",
                      "EMAIL_ADDRESS", "EMAIL_PASSWORD", "CELERY_BROKER_URL",
                      "CELERY_RESULT_BACKEND", "STRIPE_API_KEY"]:
            if getattr(self, field) is None:
                missing_fields.append(field)
        if missing_fields:
            logger.error(f"Missing required environment variables: {', '.join(missing_fields)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")


class TestingSettings(Settings):
    PATH_TO_DB: str = ":memory:"
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    EMAIL_HOSTNAME: str = "localhost"
    EMAIL_PORT: int = 1025
    EMAIL_ADDRESS: str = "test@example.com"
    EMAIL_PASSWORD: str = ""
    EMAIL_USE_TLS: bool = False
    SECRET_KEY_ACCESS: str = "test_access_key"
    SECRET_KEY_REFRESH: str = "test_refresh_key"
    CELERY_BROKER_URL: str = "memory://localhost/"
    CELERY_RESULT_BACKEND: str = "cache+memory://"
    STRIPE_API_KEY: str = "sk_test_1234567890"
    STRIPE_WEBHOOK_SECRET: str = "whsec_test_1234567890"

    def validate_settings(self):
        pass


@lru_cache()
def get_settings() -> Settings:
    """
    Retrieve the application settings based on the environment.

    Depending on the ENVIRONMENT variable (default: 'development'), returns an instance of either
    `Settings` or `TestingSettings`. Both classes inherit from `pydantic_settings.BaseSettings`
    and provide configuration parameters for the application.

    The returned object includes the following key parameters:
    - BASE_DIR: Path to the project root directory.
    - PATH_TO_DB: Path to the SQLite database file (or ':memory:' for testing).
    - PATH_TO_MOVIES_CSV: Path to the CSV file with movie data.
    - SECRET_KEY_ACCESS: Secret key for JWT access tokens.
    - SECRET_KEY_REFRESH: Secret key for JWT refresh tokens.
    - JWT_SIGNING_ALGORITHM: Algorithm used for JWT signing (default: 'HS256').
    - EMAIL_HOSTNAME: Email server hostname.
    - EMAIL_PORT: Email server port (default: 587, 1025 for testing).
    - EMAIL_ADDRESS: Email address for sending emails.
    - EMAIL_PASSWORD: Email account password.
    - EMAIL_USE_TLS: Whether to use TLS for email (default: False).
    - EMAIL_TEMPLATE_DIR: Directory for email templates (default: 'templates/email').
    - ACTIVATION_EMAIL_TEMPLATE: Template for account activation email.
    - ACTIVATION_COMPLETE_EMAIL_TEMPLATE: Template for activation confirmation email.
    - PASSWORD_EMAIL_TEMPLATE: Template for password reset request email.
    - PASSWORD_COMPLETE_EMAIL_TEMPLATE: Template for password reset confirmation email.
    - APP_BASE_URL: Base URL of the application (default: 'http://localhost:8000').
    - CELERY_BROKER_URL: URL for Celery message broker.
    - CELERY_RESULT_BACKEND: Backend for Celery task results.
    - STRIPE_API_KEY: API key for Stripe payment processing.

    :return: An instance of `Settings` (for development/production) or `TestingSettings` (for testing).
    :rtype: BaseSettings
    :raises ValidationError: If required environment variables are missing or invalid.
    :raises ValueError: If required environment variables are not set.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Loading settings for environment: {environment}")
    logger.info(f"Attempting to load .env from: {Settings.model_config['env_file']}")

    try:
        if environment == "testing":
            settings = TestingSettings()
        else:
            settings = Settings()
        settings.validate_settings()
        return settings
    except ValidationError as e:
        logger.error(f"Settings validation error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Settings error: {e}")
        raise
