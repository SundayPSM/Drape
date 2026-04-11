import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.tryon_job import TryOnStatus
from app.schemas.product import ProductResponse


class GarmentItem(BaseModel):
    image_url: str
    source_url: str
    category: str
    name: str | None = None
    fit: str = "regular"  # slim | regular | oversized


class TryOnSubmitRequest(BaseModel):
    product_id: uuid.UUID        # primary garment (for the job record FK)
    identity_id: uuid.UUID
    fit: str = "regular"
    extra_garments: list[GarmentItem] = []  # additional outfit pieces
    pose_image_url: str | None = None  # reference photo for pose + expression
    base_image_url: str | None = None  # previous result image for iterative layering


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
    fit_confidence: float | None = None
    fit_notes: str | None = None

    model_config = {"from_attributes": True}


class TryOnStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: TryOnStatus
    result_url: str | None = None
    error_message: str | None = None
