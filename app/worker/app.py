from celery import Celery
from app.config import settings


print(f"BROKER_URL: {settings.CELERY_BROKER_URL}")
print(f"BACKEND_URL: {settings.CELERY_RESULT_BACKEND}")


app = Celery(
    "booking_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)


app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
)
