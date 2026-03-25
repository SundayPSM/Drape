"""
Celery tasks for try-on background processing.
These handle fallback polling if Replicate webhooks are missed.
"""
import asyncio
import uuid
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=5)
def poll_prediction_task(self, job_id: str):
    """Fallback: poll Replicate if webhook not received within 90 seconds."""
    async def _run():
        from app.db.base import AsyncSessionFactory
        from app.db.models.tryon_job import TryOnJob, TryOnStatus
        from app.services.tryon_service import _poll_replicate

        async with AsyncSessionFactory() as db:
            job = await db.get(TryOnJob, uuid.UUID(job_id))
            if not job:
                return
            if job.status in (TryOnStatus.completed, TryOnStatus.failed):
                return  # Already resolved via webhook
            await _poll_replicate(job, db)
            await db.commit()

    asyncio.run(_run())


@celery_app.task
def schedule_fallback_poll(job_id: str):
    """Schedule a fallback poll 90 seconds after try-on submission."""
    poll_prediction_task.apply_async(args=[job_id], countdown=90)
