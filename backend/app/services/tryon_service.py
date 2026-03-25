"""
Core AI orchestration service.
Handles the full virtual try-on pipeline via Replicate IDM-VTON.
"""
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.s3 import get_public_url, upload_from_url
from app.core.exceptions import NotFoundError, ForbiddenError, DomainError
from app.db.models.tryon_job import TryOnJob, TryOnStatus
from app.db.models.identity import UserIdentity, IdentityStatus
from app.db.models.product import Product
from app.schemas.tryon import TryOnSubmitRequest, TryOnStatusResponse


async def submit_tryon(
    user_id: uuid.UUID,
    data: TryOnSubmitRequest,
    db: AsyncSession,
) -> TryOnJob:
    # Validate identity belongs to user and is ready
    identity = await db.get(UserIdentity, data.identity_id)
    if not identity or str(identity.user_id) != str(user_id):
        raise ForbiddenError("Identity not found")
    if identity.status != IdentityStatus.completed:
        raise DomainError("Identity generation not complete yet", 422)
    if not identity.s3_key:
        raise DomainError("Identity image not available", 422)

    # Validate product exists
    product = await db.get(Product, data.product_id)
    if not product or not product.is_active:
        raise NotFoundError("Product")

    human_img_url = get_public_url(identity.s3_key)
    garment_img_url = (
        get_public_url(product.image_s3_key) if product.image_s3_key else product.image_url
    )
    if not garment_img_url:
        raise DomainError("Product has no image for try-on", 422)

    # Create job record
    job = TryOnJob(
        user_id=user_id,
        product_id=data.product_id,
        identity_id=data.identity_id,
        status=TryOnStatus.processing,
        human_img_url=human_img_url,
        garment_img_url=garment_img_url,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Submit to Replicate
    webhook_url = f"{settings.app_url}/api/v1/webhooks/replicate"
    prediction_id = await _call_replicate(
        human_img_url=human_img_url,
        garment_img_url=garment_img_url,
        garment_desc=product.description or product.name,
        webhook_url=webhook_url,
    )

    job.replicate_prediction_id = prediction_id
    await db.flush()
    return job


async def _call_replicate(
    human_img_url: str,
    garment_img_url: str,
    garment_desc: str,
    webhook_url: str,
) -> str:
    """Submit prediction to Replicate and return prediction_id."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Bearer {settings.replicate_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "version": settings.replicate_tryon_version,
                "input": {
                    "human_img": human_img_url,
                    "garm_img": garment_img_url,
                    "garment_des": garment_desc[:200],
                    "is_checked": True,
                    "is_checked_crop": False,
                    "denoise_steps": 30,
                    "seed": 42,
                },
                "webhook": webhook_url,
                "webhook_events_filter": ["completed"],
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def handle_webhook(payload: dict, db: AsyncSession) -> None:
    """Process Replicate webhook callback and update job status."""
    prediction_id = payload.get("id")
    if not prediction_id:
        return

    result = await db.scalar(
        select(TryOnJob).where(TryOnJob.replicate_prediction_id == prediction_id)
    )
    if not result:
        return

    status = payload.get("status")
    if status == "succeeded":
        output = payload.get("output", [])
        output_url = output[0] if output else None
        if output_url:
            # Re-upload to our S3 for long-term storage
            s3_key = await upload_from_url(output_url, prefix=f"results/{result.user_id}")
            result.result_s3_key = s3_key
            result.result_url = get_public_url(s3_key)
        result.status = TryOnStatus.completed
        result.completed_at = datetime.now(timezone.utc)
    elif status == "failed":
        result.status = TryOnStatus.failed
        result.error_message = str(payload.get("error", "Unknown error"))

    await db.flush()


async def get_job_status(job_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> TryOnStatusResponse:
    job = await db.get(TryOnJob, job_id)
    if not job or str(job.user_id) != str(user_id):
        raise NotFoundError("Try-on job")

    # Poll Replicate if still processing and we have a prediction_id
    if job.status == TryOnStatus.processing and job.replicate_prediction_id:
        await _poll_replicate(job, db)

    return TryOnStatusResponse(
        job_id=job.id,
        status=job.status,
        result_url=job.result_url,
        error_message=job.error_message,
    )


async def _poll_replicate(job: TryOnJob, db: AsyncSession) -> None:
    """Fallback polling if webhook was missed."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"https://api.replicate.com/v1/predictions/{job.replicate_prediction_id}",
            headers={"Authorization": f"Bearer {settings.replicate_api_token}"},
        )
        if resp.status_code != 200:
            return
        await handle_webhook(resp.json(), db)


def verify_replicate_webhook(body: bytes, signature_header: str) -> bool:
    """Verify Replicate webhook HMAC signature."""
    if not settings.replicate_webhook_secret:
        return True  # skip verification in dev
    expected = hmac.new(
        settings.replicate_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


async def get_user_history(user_id: uuid.UUID, db: AsyncSession, page: int = 1, page_size: int = 20) -> list[TryOnJob]:
    result = await db.scalars(
        select(TryOnJob)
        .where(TryOnJob.user_id == user_id)
        .options(selectinload(TryOnJob.product))
        .order_by(TryOnJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result)


async def save_look(job_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> TryOnJob:
    job = await db.get(TryOnJob, job_id)
    if not job or str(job.user_id) != str(user_id):
        raise NotFoundError("Try-on job")
    job.is_saved = True
    if not job.share_slug:
        job.share_slug = str(uuid.uuid4())[:8]
    await db.flush()
    return job
