import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.photo import UserPhoto
from app.dependencies import get_current_user
from app.schemas.user import UserResponse, PhotoResponse, IdentityResponse, ProfileUpdateRequest
from app.core.s3 import generate_presigned_upload, get_public_url
from app.services import identity_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/profile", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save body profile info: gender, height, weight, size, skin tone."""
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.get("/me/photos", response_model=list[PhotoResponse])
async def get_my_photos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    photos = list(await db.scalars(
        select(UserPhoto)
        .where(UserPhoto.user_id == current_user.id)
        .order_by(UserPhoto.sort_order)
    ))
    result = []
    for p in photos:
        r = PhotoResponse.model_validate(p)
        r.url = get_public_url(p.s3_key)
        result.append(r)
    return result


@router.post("/me/photos/presign")
async def presign_photo_upload(
    photo_type: str = "general",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a presigned Supabase Storage URL for direct browser upload."""
    GUIDED_TYPES = {"face_front", "profile_left", "profile_right", "body_front", "body_side", "three_quarter"}
    prefix = f"photos/{current_user.id}/original" if photo_type in GUIDED_TYPES else f"photos/{current_user.id}"
    data = generate_presigned_upload(prefix=prefix)

    photo = UserPhoto(
        user_id=current_user.id,
        s3_key=data["key"],
        photo_type=photo_type,
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)

    return {
        "photo_id": photo.id,
        "key": data["key"],
        "presigned": data["presigned"],
    }


@router.get("/me/identity", response_model=IdentityResponse | None)
async def get_my_identity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    identity = await identity_service.get_active_identity(current_user.id, db)
    if not identity:
        return None
    return identity_service.enrich_identity(identity)


@router.post("/me/identity/generate")
async def generate_identity(
    photo_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate 4 AI portrait candidates via Gemini (Nano Banana 2).
    Returns candidates for the user to pick from — identity is NOT saved yet.
    """
    result = await identity_service.generate_candidates(current_user.id, photo_ids, db)
    return result


@router.post("/me/identity/confirm", response_model=IdentityResponse, status_code=201)
async def confirm_identity(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save the user's chosen AI portrait as their active identity."""
    s3_key = body.get("s3_key")
    photo_ids = [uuid.UUID(pid) for pid in body.get("photo_ids", [])]

    if not s3_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="s3_key is required")

    identity = await identity_service.confirm_identity(current_user.id, s3_key, photo_ids, db)
    return identity_service.enrich_identity(identity)
