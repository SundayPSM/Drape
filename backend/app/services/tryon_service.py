"""
Core AI orchestration service.
Handles the full virtual try-on pipeline via Gemini image generation.
"""
import asyncio
import uuid
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.gemini import generate_tryon, GarmentInput, SubjectProfile
from app.core.s3 import get_public_url, upload_bytes
from app.core.exceptions import NotFoundError, ForbiddenError, DomainError
from app.db.models.tryon_job import TryOnJob, TryOnStatus
from app.db.models.identity import UserIdentity, IdentityStatus
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.tryon import TryOnSubmitRequest, TryOnStatusResponse

_log = logging.getLogger(__name__)


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

    # Load user profile for body proportions
    user = await db.get(User, user_id)
    subject = SubjectProfile(
        height_cm=user.height_cm or 170,
        weight_kg=user.weight_kg or 70,
        gender=user.gender or "person",
        age=user.age or 25,
        body_type=user.body_type or "",
    ) if user else None

    # Validate product exists
    product = await db.get(Product, data.product_id)
    if not product or not product.is_active:
        raise NotFoundError("Product")

    identity_img_url = get_public_url(identity.s3_key)
    # Iterative layering: use previous result as the person base if provided
    human_img_url = data.base_image_url if data.base_image_url else identity_img_url
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

    # Collect all URLs to download: [person, pose_ref?, primary_garment, ...extras]
    primary_category = product.category.value if hasattr(product.category, "value") else str(product.category)
    primary_fit = data.fit if data.fit in ("slim", "regular", "oversized") else "regular"
    primary_desc = product.description or product.name or primary_category

    all_urls = [human_img_url]
    if data.pose_image_url:
        all_urls.append(data.pose_image_url)
    all_urls.append(garment_img_url)
    for g in data.extra_garments:
        all_urls.append(g.image_url)

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            fetched = await asyncio.gather(*[client.get(u) for u in all_urls])
        for r in fetched:
            r.raise_for_status()
    except Exception as exc:
        job.status = TryOnStatus.failed
        job.error_message = f"Failed to download images: {exc}"
        await db.flush()
        return job

    idx = 0
    person_bytes = fetched[idx].content; idx += 1
    pose_bytes: bytes | None = None
    if data.pose_image_url:
        pose_bytes = fetched[idx].content; idx += 1

    garments: list[GarmentInput] = [
        GarmentInput(
            image_bytes=fetched[idx].content,
            category=primary_category,
            fit=primary_fit,
            description=primary_desc[:300],
        )
    ]
    idx += 1
    for extra in data.extra_garments:
        garments.append(GarmentInput(
            image_bytes=fetched[idx].content,
            category=extra.category,
            fit=extra.fit if extra.fit in ("slim", "regular", "oversized") else "regular",
            description=(extra.name or extra.category)[:300],
        ))
        idx += 1

    _log.info(
        "Starting Gemini try-on for job %s (%d garments, pose_ref=%s, layering=%s, height=%scm)",
        job.id, len(garments), bool(pose_bytes), bool(data.base_image_url), subject.height_cm if subject else "?"
    )

    result_bytes = await generate_tryon(
        person_bytes=person_bytes,
        garments=garments,
        pose_bytes=pose_bytes,
        subject=subject,
    )

    if not result_bytes:
        job.status = TryOnStatus.failed
        job.error_message = "AI try-on generation failed. Please try again."
        await db.flush()
        return job

    # Upload result to Supabase Storage
    result_key = await upload_bytes(result_bytes, prefix=f"results/{user_id}")
    job.result_s3_key = result_key
    job.result_url = get_public_url(result_key)
    job.status = TryOnStatus.completed
    job.completed_at = datetime.now(timezone.utc)
    await db.flush()
    _log.info("Try-on job %s completed successfully", job.id)
    return job



async def get_job_status(job_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> TryOnStatusResponse:
    job = await db.get(TryOnJob, job_id)
    if not job or str(job.user_id) != str(user_id):
        raise NotFoundError("Try-on job")

    return TryOnStatusResponse(
        job_id=job.id,
        status=job.status,
        result_url=job.result_url,
        error_message=job.error_message,
    )


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
