import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, DateTime, func, Enum, DECIMAL, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        Enum(PaymentStatusEnum),
        nullable=False,
        default=PaymentStatusEnum.PENDING
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )
    external_payment_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        unique=True
    )

    user: Mapped["UserModel"] = relationship(back_populates="payments")
    order: Mapped["Orders"] = relationship(back_populates="payments")
    payment_items: Mapped[list["PaymentItem"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False
    )
    price_at_payment: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )

    payment: Mapped["Payment"] = relationship(back_populates="payment_items")
    order_item: Mapped["OrderItems"] = relationship(back_populates="payment_items")
