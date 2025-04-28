from datetime import datetime
from typing import List

from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class CartModel(Base):
    __tablename__ = "carts"
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
        unique=True
    )
    user: Mapped["Users"] = relationship(
        "Users",
        back_populates="cart",
        uselist=False
    )
    cart_items: Mapped[List["CartItemsModel"]] = relationship(
        "CartItems",
        back_populates="cart",
        cascade="all, delete-orphan"
    )


class CartItemsModel(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "carts.id",
            ondelete="CASCADE"
        )
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE"
        )
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )

    cart: Mapped["CartModel"] = relationship(
        "Carts",
        back_populates="cart_items"
    )
    movie: Mapped["Movies"] = relationship(
        "Movies",
        back_populates="cart_items"
    )

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "movie_id",
            name="unique_cart_movie"
        ),
    )