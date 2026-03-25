import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.tryon_job import TryOnStatus
from app.schemas.product import ProductResponse


class TryOnSubmitRequest(BaseModel):
    product_id: uuid.UUID
    identity_id: uuid.UUID


class TryOnJobResponse(BaseModel):
    id: uuid.UUID
    status: TryOnStatus
    product: ProductResponse | None = None
    result_url: str | None
    human_img_url: str | None
    is_saved: bool
    share_slug: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TryOnStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: TryOnStatus
    result_url: str | None = None
    error_message: str | None = None
