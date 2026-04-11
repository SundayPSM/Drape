import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.base import Base


class TryOnStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TryOnJob(Base):
    __tablename__ = "tryon_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_identities.id"))

    replicate_prediction_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[TryOnStatus] = mapped_column(SAEnum(TryOnStatus, name="tryon_status"), default=TryOnStatus.pending)

    human_img_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    garment_img_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    result_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    share_slug: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="tryon_jobs")  # noqa: F821
    product: Mapped["Product"] = relationship(back_populates="tryon_jobs")  # noqa: F821
