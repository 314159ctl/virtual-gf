"""用户模型"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    membership_tier: Mapped[str] = mapped_column(String(20), default="free")  # free / premium / vip
    membership_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    must_change_password: Mapped[bool] = mapped_column(default=False)

    # 关系
    characters = relationship("Character", back_populates="owner", lazy="dynamic")
    conversations = relationship("Conversation", back_populates="user", lazy="dynamic")
