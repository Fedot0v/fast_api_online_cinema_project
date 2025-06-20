import enum
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    String,
    Enum,
    Integer,
    Boolean,
    DateTime,
    func,
    ForeignKey, Date, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.database.models.base import Base
from src.database.validators import accounts as validators
from src.security.passwords import hash_password, verify_password
from src.security.utils import generate_secure_token
from src.database.models.movies import (
    CommentLikeModel,
    MovieLikeModel,
    MovieRatingModel,
    MovieCommentModel,
    MovieFavoriteModel
)
from src.database.models.notifications import NotificationModel
from src.database.models.cart import CartModel
from src.database.models.orders import Orders
from src.database.models.payments import Payment


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        Enum(UserGroupEnum),
        nullable=False,
        unique=True
    )
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        back_populates="group"
    )

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password",
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    group: Mapped["UserGroupModel"] = relationship(
        back_populates="users"
    )
    activation_token: Mapped[Optional["ActivationTokenModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_reset_token: Mapped[Optional["PasswordResetTokenModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    movie_likes: Mapped[List["MovieLikeModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    movie_ratings: Mapped[List["MovieRatingModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    movie_comments: Mapped[List["MovieCommentModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    movie_favorites: Mapped[List["MovieFavoriteModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    comment_likes: Mapped[List["CommentLikeModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["NotificationModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[NotificationModel.user_id]"
    )
    notifications_trigger: Mapped[List["NotificationModel"]] = relationship(
        back_populates="trigger_user",
        cascade="all, delete-orphan",
        foreign_keys="[NotificationModel.trigger_user_id]"
    )
    cart: Mapped["CartModel"] = relationship(
        back_populates="user",
        uselist=False
    )
    orders: Mapped[List["Orders"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return (f"<UserModel(id={self.id}, email={self.email}, "
                f"is_active={self.is_active})>")

    def has_group(self, group_name: UserGroupEnum) -> bool:
        return self.group.name == group_name

    @classmethod
    def create(
            cls,
            email: str,
            raw_password: str,
            group_id: int | Mapped[int]
    ) -> "UserModel":
        """
        Factory method to create a new UserModel instance.
        This method simplifies the creation of a new user by handling
        password hashing and setting required attributes.
        """
        user = cls(email=email, group_id=group_id)
        user.password = raw_password
        return user

    @property
    def password(self) -> None:
        raise AttributeError(
            "Password is write-only. Use the setter to set the password."
        )

    @password.setter
    def password(self, raw_password: str) -> None:
        """
        Set the user's password after validating its strength and hashing it.
        """
        validators.validate_password_strength(raw_password)
        self._hashed_password = hash_password(raw_password)

    @validates("email")
    def validate_email(self, key, value):
        return validators.validate_email(value.lower())

    def verify_password(self, raw_password: str) -> bool:
        """
        Verify the provided password against the stored hashed password.
        """
        return verify_password(raw_password, self._hashed_password)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    _avatar: Mapped[Optional[str]] = mapped_column("avatar", String(255))
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum)
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    info: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="profile"
    )

    def __repr__(self):
        return (
            f"<UserProfileModel(id={self.id}, first_name={self.first_name},"
            f" last_name={self.last_name}, "
            f"gender={self.gender}, date_of_birth={self.date_of_birth})>"
        )

    @property
    def avatar(self) -> Optional[str]:
        return self._avatar

    @avatar.setter
    def avatar(self, value: Optional[Path | str]) -> None:
        """
        Convert WindowsPath to string before saving to avatar field.
        """
        if isinstance(value, Path):
            self._avatar = value.as_posix()
        else:
            self._avatar = value


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        default=generate_secure_token,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1)
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="activation_token"
    )

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return (f"<ActivationTokenModel(id={self.id}, token={self.token},"
                f" expires_at={self.expires_at})>")


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="password_reset_token"
    )

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return (f"<PasswordResetTokenModel(id={self.id}, token={self.token},"
                f" expires_at={self.expires_at})>")


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="refresh_tokens"
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        default=generate_secure_token
    )

    @classmethod
    def create(
            cls,
            user_id: int | Mapped[int],
            days_valid: int,
            token: str
    ) -> "RefreshTokenModel":
        """
        Factory method to create a new RefreshTokenModel instance.

        This method simplifies the creation of a new refresh token by calculating
        the expiration date based on the provided number of valid days and setting
        the required attributes.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
        return cls(user_id=user_id, expires_at=expires_at, token=token)

    def __repr__(self):
        return (f"<RefreshTokenModel(id={self.id}, token={self.token},"
                f" expires_at={self.expires_at})>")
