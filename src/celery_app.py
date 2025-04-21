from celery import Celery

from src.celery_beat_schedule import CELERY_BEAT_SCHEDULE
from src.config.settings import get_settings


settings = get_settings()

celery_app = Celery(
    "online_cinema",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.accounts"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule=CELERY_BEAT_SCHEDULE
)