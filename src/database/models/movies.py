from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, ForeignKey, Float, DECIMAL, Text, UniqueConstraint, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, MANYTOMANY, relationship, validates

from src.database.models.base import Base
from src.database.utils import with_normalized_name_events


class MovieGenreModel(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movie.id",
            ondelete="CASCADE",
        ),
        primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "genre.id",
            ondelete="CASCADE",
        ),
        primary_key=True
    )


class MovieDirectorModel(Base):
    __tablename__ = "movie_directors"

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movie.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    director_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "director.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )


class MovieStarModel(Base):
    __tablename__ = "movie_stars"

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movie.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    star_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "star.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )


@with_normalized_name_events
class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    normalized_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )

    movies: Mapped[List["MovieModel"]] = relationship(
        secondary=MovieGenreModel.__table__,
        back_populates="genres",
        cascade="all, delete"
    )


@with_normalized_name_events
class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    normalized_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    movies: Mapped[List["MovieModel"]] = relationship(
        secondary=MovieStarModel.__table__,
        back_populates="stars",
        cascade="all, delete"
    )


@with_normalized_name_events
class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    normalized_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    movies: Mapped[List["MovieModel"]] = relationship(
        secondary=MovieDirectorModel.__table__,
        back_populates="directors",
        cascade="all, delete"
    )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    movies: Mapped[List["MovieModel"]] = relationship(
        back_populates="certifications",
        cascade="all, delete"
    )


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    uuid: Mapped[UUID] = mapped_column(
        unique=True,
        nullable=False,
        default=uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    time: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    imdb: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    meta_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    gross: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )
    certification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(
            "certifications.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "year",
            "time",
            name="movie_name_year_time"
        )
    )

    certification: Mapped["CertificationModel"] = relationship(
        back_populates="movies",
    )
    genres: Mapped[List["GenreModel"]] = relationship(
        secondary=MovieGenreModel.__table__,
        back_populates="movies",
        cascade="all, delete"
    )
    directors: Mapped[List["DirectorModel"]] = relationship(
        secondary=MovieDirectorModel.__table__,
        back_populates="directors",
        cascade="all, delete"
    )
    stars: Mapped[List["StarModel"]] = relationship(
        secondary=MovieStarModel.__table__,
        back_populates="stars",
        cascade="all, delete"
    )
    likes: Mapped[List["MovieLikeModel"]] = relationship(
        "MovieLikeModel",
        back_populates="movie",
        cascade="all, delete"
    )
    ratings: Mapped[List["MovieRatingModel"]] = relationship(
        "MovieRatingModel",
        back_populates="movie",
        cascade="all, delete"
    )
    favorites: Mapped[List["MovieFavoriteModel"]] = relationship(
        "MovieFavoriteModel",
        back_populates="movie",
        cascade="all, delete"
    )
    comments: Mapped[List["MovieCommentModel"]] = relationship(
        "MovieCommentModel",
        back_populates="movie",
        cascade="all, delete"
    )
    cart_items: Mapped[List["CartItemsModel"]] = relationship(
        "CartItems",
        back_populates="movie",
        cascade="all, delete-orphan"
    )
    order_items: Mapped[List["OrderItems"]] = relationship(
        "OrderItems",
        back_populates="movie",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class MovieCommentModel(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE"
        ),
        nullable=False
    ),
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    parent_comment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "comments.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="movie_comments"
    )
    movie: Mapped["MovieModel"] = relationship(
        back_populates="comments"
    )
    likes: Mapped[List["CommentLikeModel"]] = relationship(
        back_populates="comment",
        cascade="all, delete"
    )
    notifications: Mapped[List["NotificationModel"]] = relationship(
        back_populates="comment",
        cascade="all, delete"
    )
    parent: Mapped[Optional["MovieCommentModel"]] = relationship(
        back_populates="replies",
        remote_side=[id]
    )


class MovieLikeModel(Base):
    __tablename__ = "movie_likes"
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    is_like: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_like"
        )
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="movie_likes"
    )
    movie: Mapped["MovieModel"] = relationship(
        back_populates="likes"
    )


class MovieRatingModel(Base):
    __tablename__ = "movie_ratings"
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    @validates("rating")
    def validate_rating(self, key, value):
        if not 1 <= value <= 10:
            raise ValueError("Rating must be between 1 and 10.")
        return value

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_rating"
        )
    )

    user: Mapped["UserModel"] = relationship(
        back_populates="movie_ratings"
    )
    movie: Mapped["MovieModel"] = relationship(
        back_populates="ratings"
    )


class MovieFavoriteModel(Base):
    __tablename__ = "movie_favorites"
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_favorite"
        )
    )
    user: Mapped["UserModel"] = relationship(
        back_populates="movie_favorites"
    )
    movie: Mapped["MovieModel"] = relationship(
        back_populates="favorites"
    )