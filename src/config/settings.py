import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "movies.db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")
    SECRET_KEY_ACCESS: str
    SECRET_KEY_REFRESH: str
    JWT_SIGNING_ALGORITHM: str = "HS256"
    EMAIL_HOSTNAME: str
    EMAIL_PORT: int = 587
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    EMAIL_USE_TLS: bool = False
    EMAIL_TEMPLATE_DIR: str = "templates/email"
    ACTIVATION_EMAIL_TEMPLATE: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE: str = "activation_complete.html"
    PASSWORD_EMAIL_TEMPLATE: str = "password_reset_request.html"
    PASSWORD_COMPLETE_EMAIL_TEMPLATE: str = "password_reset_complete.html"
    APP_BASE_URL: str = "http://localhost:8000"
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

class TestingSettings(Settings):
    PATH_TO_DB: str = ":memory:"
    EMAIL_HOSTNAME: str = "localhost"
    EMAIL_PORT: int = 1025
    EMAIL_ADDRESS: str = "test@example.com"
    EMAIL_PASSWORD: str = ""
    EMAIL_USE_TLS: bool = False
    SECRET_KEY_ACCESS: str = "test_access_key"  # Значение для тестов
    SECRET_KEY_REFRESH: str = "test_refresh_key"  # Значение для тестов

def get_settings() -> BaseSettings:
    """
    Retrieve the application settings based on the environment.

    :return: An instance of the appropriate settings class.
    :rtype: BaseSettings
    """
    environment = os.getenv("ENVIRONMENT", "development")  # Изменено на "development"
    if environment == "testing":
        return TestingSettings()
    return Settings()