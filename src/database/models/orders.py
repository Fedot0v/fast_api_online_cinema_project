import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import ForeignKey, Integer, DateTime, Enum, DECIMAL, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(),
        server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        Enum(OrderStatusEnum),
        nullable=False,
        default=OrderStatusEnum.PENDING
    )
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(back_populates="orders")
    order_items: Mapped[list["OrderItems"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class OrderItems(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "orders.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )
    price_at_order: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    order: Mapped["Orders"] = relationship(back_populates="order_items")
    movie: Mapped["MovieModel"] = relationship(lazy="selectin")
    payment_items: Mapped[List["PaymentItem"]] = relationship(
        back_populates="order_item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
