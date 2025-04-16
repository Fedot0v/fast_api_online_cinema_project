import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "movies.db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"


class TestingSettings(Settings):
    PATH_TO_DB: str = ":memory:"


def get_settings() -> BaseSettings:
    """
    Retrieve the application settings based on the environment.

    This function checks the `ENVIRONMENT` environment variable to determine
    which settings class to use. If `ENVIRONMENT` is set to `"testing"`, it
    returns an instance of `TestingSettings`. Otherwise, it defaults to `Settings`.

    :return: An instance of the appropriate settings class.
    :rtype: BaseSettings
    """
    environment = os.getenv("ENVIRONMENT", "testing")
    if environment == "testing":
        return TestingSettings()
    return Settings()
