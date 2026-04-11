import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    avatar_url: str | None
    gender: str | None = None
    age: int | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    usual_size: str | None = None
    skin_tone: str | None = None
    body_type: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    gender: str | None = None
    age: int | None = None
    height_cm: int | None = None
    weight_kg: int | None = None
    usual_size: str | None = None
    skin_tone: str | None = None


class PhotoResponse(BaseModel):
    id: uuid.UUID
    s3_key: str
    photo_type: str
    sort_order: int
    url: str | None = None  # populated by service

    model_config = {"from_attributes": True}


class IdentityResponse(BaseModel):
    id: uuid.UUID
    status: str
    image_url: str | None = None  # populated by service
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
