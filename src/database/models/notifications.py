import enum
from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from src.database.models.base import Base


class NotificationType(str, enum.Enum):
    COMMENT_REPLY = "comment_reply"
    FAVORITE_ADDED = "favorite_added"


class NotificationModel(Base):
    __tablename__ = "notifications"

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
        nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False
    )
    comment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "comments.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )
    trigger_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    user: Mapped["UserModel"] = relationship(
        foreign_keys=[user_id],
        back_populates="notifications"
    )
    trigger_user: Mapped["UserModel"] = relationship(
        foreign_keys=[trigger_user_id],
        back_populates="notifications_trigger"
    )
    comment: Mapped["MovieCommentModel"] = relationship(
        back_populates="notifications"
    )
