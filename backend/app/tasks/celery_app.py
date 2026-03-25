from celery import Celery
from app.config import settings

celery_app = Celery(
    "drape",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.tryon_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=120,
    task_time_limit=180,
)
