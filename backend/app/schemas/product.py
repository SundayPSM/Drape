import uuid
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from app.db.models.product import ProductCategory


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    brand: str | None
    description: str | None
    category: ProductCategory
    price: float | None
    currency: str
    image_url: str | None
    source_url: str | None
    affiliate_url: str | None
    is_curated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScrapeRequest(BaseModel):
    url: str


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
