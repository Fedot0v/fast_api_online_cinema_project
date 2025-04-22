from typing import List, Optional
from uuid import UUID

from sqlalchemy import Integer, String, ForeignKey, Float, DECIMAL, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, MANYTOMANY, relationship

from src.database.models.base import Base


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
    movies: Mapped[List["MovieModel"]] = relationship(
        secondary=MovieGenreModel.__table__,
        back_populates="genres",
        cascade="all, delete"
    )


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
    movies: Mapped[List["MovieModel"]] = relationship(
        secondary=MovieStarModel.__table__,
        back_populates="stars",
        cascade="all, delete"
    )


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
        nullable=False
    )
    name: Mapped[str] = mapped_column(
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
    price: Mapped[float] = mapped_column(
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
