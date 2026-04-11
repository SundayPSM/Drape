"""
User identity generation service — two-phase pipeline.

Phase 0: Analyze body type from reference photos via Gemini text.
Phase 1: Expand 6 guided photos into 10 synthetic angle fills via Gemini.
         All 10 saved to Supabase Storage (photos/{user_id}/angles/).
Phase 2: Generate 4 final try-on portraits from all 16 images via Gemini.
         4 candidates saved to identities/{user_id}/candidates/.
User picks one → confirm_identity() saves it as the active identity.
"""
import asyncio
import uuid
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import DomainError
from app.core.s3 import get_public_url, upload_bytes
from app.core.gemini import (
    analyze_body_type,
    generate_angle_variations,
    generate_identity_candidates,
    UserProfile,
)
from app.db.models.identity import UserIdentity, IdentityStatus
from app.db.models.photo import UserPhoto
from app.db.models.user import User
from app.schemas.user import IdentityResponse

MIN_ANGLES = 4  # abort if fewer than this succeed in Phase 1


async def generate_candidates(
    user_id: uuid.UUID,
    photo_ids: list[uuid.UUID],
    db: AsyncSession,
) -> dict:
    """
    Full pipeline: body analysis → angle generation → portrait generation.

    Returns:
        {
          "body_type": str,
          "angles": [{"key": str, "image_url": str}, ...],   # 10 images
          "candidates": [{"key": str, "image_url": str}, ...] # 4 portraits
        }
    """
    if len(photo_ids) != 6:
        raise DomainError("All 6 guided photos are required to generate your identity.", 422)

    # ── Load user ────────────────────────────────────────────────────────────
    user = await db.get(User, user_id)

    # ── Fetch the 6 guided photos from DB ────────────────────────────────────
    photos = list(await db.scalars(
        select(UserPhoto)
        .where(UserPhoto.user_id == user_id, UserPhoto.id.in_(photo_ids))
    ))
    if len(photos) != 6:
        raise DomainError("Could not find all 6 provided photos.", 422)

    # ── Download all 6 originals from Supabase Storage ───────────────────────
    async with httpx.AsyncClient(timeout=60) as client:
        responses = await asyncio.gather(
            *[client.get(get_public_url(p.s3_key)) for p in photos]
        )
    reference_images: list[bytes] = []
    for resp in responses:
        resp.raise_for_status()
        reference_images.append(resp.content)

    # ── Phase 0: Detect body type from photos ────────────────────────────────
    detected_body_type = await analyze_body_type(reference_images, user.gender or "person")

    # Persist detected body type on the user record
    user.body_type = detected_body_type
    await db.flush()

    # ── Build profile ────────────────────────────────────────────────────────
    profile = UserProfile(
        gender=user.gender or "person",
        age=user.age or 25,
        height_cm=user.height_cm or 170,
        weight_kg=user.weight_kg or 65,
        skin_tone=user.skin_tone or "medium",
        body_type=detected_body_type,
    )

    # ── Phase 1: Generate 10 angle variations ────────────────────────────────
    angle_bytes_list = await generate_angle_variations(reference_images, profile)

    if len(angle_bytes_list) < MIN_ANGLES:
        raise DomainError(
            f"Angle generation produced too few results ({len(angle_bytes_list)}/{MIN_ANGLES} minimum). "
            "Please try again.",
            500,
        )

    # Save angles to storage
    angles: list[dict] = []
    for img in angle_bytes_list:
        key = await upload_bytes(
            data=img,
            prefix=f"photos/{user_id}/angles",
            content_type="image/jpeg",
        )
        angles.append({"key": key, "image_url": get_public_url(key)})

    # ── Phase 2: Generate 4 final portraits from the 6 originals only ────────
    # Passing all 16 images exceeds model limits — originals are sufficient
    candidate_bytes_list = await generate_identity_candidates(reference_images, profile)

    if not candidate_bytes_list:
        raise DomainError("AI portrait generation failed. Please try again.", 500)

    # Save final candidates to storage
    candidates: list[dict] = []
    for img in candidate_bytes_list:
        key = await upload_bytes(
            data=img,
            prefix=f"identities/{user_id}/candidates",
            content_type="image/jpeg",
        )
        candidates.append({"key": key, "image_url": get_public_url(key)})

    return {
        "body_type": detected_body_type,
        "angles": angles,
        "candidates": candidates,
    }


async def confirm_identity(
    user_id: uuid.UUID,
    s3_key: str,
    source_photo_ids: list[uuid.UUID],
    db: AsyncSession,
) -> UserIdentity:
    """Persist the user's chosen candidate as their active identity."""
    prev = list(await db.scalars(
        select(UserIdentity).where(
            UserIdentity.user_id == user_id,
            UserIdentity.is_active == True,  # noqa: E712
        )
    ))
    for p in prev:
        p.is_active = False

    identity = UserIdentity(
        user_id=user_id,
        status=IdentityStatus.completed,
        s3_key=s3_key,
        source_photo_ids=",".join(str(pid) for pid in source_photo_ids),
        is_active=True,
    )
    db.add(identity)
    await db.flush()
    await db.refresh(identity)
    return identity


async def get_active_identity(user_id: uuid.UUID, db: AsyncSession) -> UserIdentity | None:
    return await db.scalar(
        select(UserIdentity).where(
            UserIdentity.user_id == user_id,
            UserIdentity.is_active == True,  # noqa: E712
            UserIdentity.status == IdentityStatus.completed,
        )
    )


def enrich_identity(identity: UserIdentity) -> IdentityResponse:
    resp = IdentityResponse.model_validate(identity)
    if identity.s3_key:
        resp.image_url = get_public_url(identity.s3_key)
    return resp
