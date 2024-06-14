import os

from celery import Celery


celery = Celery("background_worker")

celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:16379")  #
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:16379")  #

celery.conf.update(
    timezone="Europe/Moscow",
    enable_utc=False,
)

