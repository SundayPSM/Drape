import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Float, Text, Enum as SAEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.base import Base


class ProductCategory(str, enum.Enum):
    tops = "tops"
    bottoms = "bottoms"
    dresses = "dresses"
    outerwear = "outerwear"
    footwear = "footwear"
    accessories = "accessories"
    watches = "watches"
    sunglasses = "sunglasses"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[ProductCategory] = mapped_column(SAEnum(ProductCategory, name="product_category"), default=ProductCategory.tops)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    image_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # original URL
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    affiliate_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    affiliate_network: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_curated: Mapped[bool] = mapped_column(Boolean, default=False)  # hand-picked catalog
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tryon_jobs: Mapped[list["TryOnJob"]] = relationship(back_populates="product")  # noqa: F821
