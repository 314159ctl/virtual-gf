"""支付 & 用量模型"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin, TimestampMixin


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe / alipay / wechat
    provider_payment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    tier_purchased: Mapped[str] = mapped_column(String(20), nullable=False)  # premium / vip
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / completed / refunded


class UsageLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "api_usage_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(100))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    model: Mapped[str | None] = mapped_column(String(100))
    cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
