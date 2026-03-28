import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Supabase Auth user ID — this is the `sub` from the JWT
    supabase_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    photos: Mapped[list["UserPhoto"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    identities: Mapped[list["UserIdentity"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    tryon_jobs: Mapped[list["TryOnJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
