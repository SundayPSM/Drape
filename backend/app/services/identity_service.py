"""
User identity generation service.
Strategy A (MVP): Use the best-quality photo as the canonical identity image.
Strategy B (Enhanced): Submit to Replicate consistent-character model.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundError, ForbiddenError, DomainError
from app.core.s3 import get_public_url
from app.db.models.identity import UserIdentity, IdentityStatus
from app.db.models.photo import UserPhoto
from app.schemas.user import IdentityResponse


async def generate_identity(
    user_id: uuid.UUID,
    photo_ids: list[uuid.UUID],
    db: AsyncSession,
) -> UserIdentity:
    if len(photo_ids) < 4:
        raise DomainError("At least 4 photos are required to generate your identity", 422)

    # Fetch photos belonging to this user
    photos = list(await db.scalars(
        select(UserPhoto)
        .where(UserPhoto.user_id == user_id, UserPhoto.id.in_(photo_ids))
        .order_by(UserPhoto.sort_order)
    ))

    if len(photos) < 4:
        raise DomainError("Could not find all provided photos", 422)

    # Deactivate previous identities
    prev = list(await db.scalars(
        select(UserIdentity).where(UserIdentity.user_id == user_id, UserIdentity.is_active == True)  # noqa: E712
    ))
    for p in prev:
        p.is_active = False

    # Strategy A: Use the front-view photo (or first photo) as canonical image
    front_photo = next(
        (p for p in photos if p.photo_type == "front"),
        photos[0],
    )

    identity = UserIdentity(
        user_id=user_id,
        status=IdentityStatus.completed,  # Strategy A: immediate
        s3_key=front_photo.s3_key,
        source_photo_ids=",".join(str(p.id) for p in photos),
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
