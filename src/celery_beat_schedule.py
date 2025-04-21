from celery.schedules import crontab


CELERY_BEAT_SCHEDULE = {
    "clean-expired-tokens": {
        "task": "src.tasks.clean_expired_tokens",
        "schedule": crontab(minute=0, hour=0),
    }
}
