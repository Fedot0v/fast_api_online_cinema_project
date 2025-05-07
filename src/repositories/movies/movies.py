from typing import List, Sequence, Optional, Dict

from sqlalchemy import select, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models.movies import (
    MovieModel,
    MovieGenreModel,
    GenreModel,
    MovieStarModel,
    StarModel,
    MovieDirectorModel,
    DirectorModel,
    CertificationModel
)
from src.database.utils import normalize_name
from src.repositories.base import BaseRepository
from src.schemas.movies import (
    MovieBase,
    MovieDetail,
    MovieQuery,
    MovieCreateSchema,
    MovieUpdateSchema,
)


class MovieRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_movies(
            self,
            skip: int = 0,
            limit: int = 10,
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ) -> Sequence[MovieModel]:
        stmt = select(MovieModel).options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars)
        )
        if sort_by:
            sort_attr = getattr(MovieModel, sort_by, None)
            if sort_attr is None:
                raise ValueError(f"Invalid sort_by attribute: {sort_by}")
            stmt = stmt.order_by(
                asc(sort_attr) if sort_order == "asc" else desc(sort_attr)
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_movie_by_id(self, movie_id: int) -> MovieModel:
        stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
            joinedload(MovieModel.genres),  # Загрузка жанров
            joinedload(MovieModel.directors),  # Загрузка режиссеров
            joinedload(MovieModel.stars)  # Загрузка актеров
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().first()

    async def filter_movies(
            self,
            filters: Dict[str, any] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "asc",
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> Sequence[MovieModel]:
        stmt = select(MovieModel).options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars)
        )
        if filters:
            if "year" in filters:
                stmt = stmt.where(MovieModel.year == filters["year"])
            if "year_min" in filters:
                stmt = stmt.where(MovieModel.year >= filters["year_min"])
            if "year_max" in filters:
                stmt = stmt.where(MovieModel.year <= filters["year_max"])
            if "imdb_min" in filters:
                stmt = stmt.where(MovieModel.imdb >= filters["imdb_min"])
            if "imdb_max" in filters:
                stmt = stmt.where(MovieModel.imdb <= filters["imdb_max"])
            if "price_min" in filters:
                stmt = stmt.where(MovieModel.price >= filters["price_min"])
            if "price_max" in filters:
                stmt = stmt.where(MovieModel.price <= filters["price_max"])
        if sort_by:
            sort_attr = getattr(MovieModel, sort_by, None)
            if sort_attr is None:
                raise ValueError(f"Invalid sort_by attribute: {sort_by}")
            stmt = stmt.order_by(
                asc(sort_attr) if sort_order == "asc" else desc(sort_attr)
            )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def search_movies(
            self,
            search_criteria: Dict[str, str] = None,
            partial_match: bool = True,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> Sequence[MovieModel]:
        """
        Search movies by multiple criteria (title, description, actor, director, genre).
        """
        stmt = select(MovieModel).distinct().options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars)
        )

        if search_criteria:
            valid_criteria = {
                "title",
                "description",
                "actor",
                "director",
                "genre"
            }
            invalid_criteria = set(search_criteria) - valid_criteria
            if invalid_criteria:
                raise ValueError(
                    f"Invalid search criteria: {invalid_criteria}"
                )

            if "title" in search_criteria:
                query = (
                    normalize_name(search_criteria["title"])
                ) if partial_match else (
                    search_criteria["title"].lower().strip()
                )
                stmt = stmt.filter(
                    MovieModel.title.contains(query)
                    if partial_match else MovieModel.title.ilike(query)
                )

            if "description" in search_criteria:
                query = (
                    normalize_name(search_criteria["description"])
                ) if partial_match else (
                    search_criteria["description"].lower().strip()
                )
                stmt = stmt.filter(
                    MovieModel.description.contains(query)
                    if partial_match else MovieModel.description.ilike(query)
                )

            if "actor" in search_criteria:
                query = (
                    normalize_name(search_criteria["actor"])
                ) if partial_match else (
                    search_criteria["actor"].lower().strip()
                )
                stmt = stmt.join(
                    MovieStarModel,
                    MovieStarModel.movie_id == MovieModel.id
                )
                stmt = stmt.join(
                    StarModel,
                    StarModel.id == MovieStarModel.star_id
                )
                stmt = stmt.filter(
                    StarModel.normalized_name.contains(query)
                    if partial_match else StarModel.normalized_name == query
                )

            if "director" in search_criteria:
                query = (
                    normalize_name(search_criteria["director"])
                ) if partial_match else (
                    search_criteria["director"].lower().strip()
                )
                stmt = stmt.join(
                    MovieDirectorModel,
                    MovieDirectorModel.movie_id == MovieModel.id
                )
                stmt = stmt.join(
                    DirectorModel,
                    DirectorModel.id == MovieDirectorModel.director_id
                )
                stmt = stmt.filter(
                    DirectorModel.normalized_name.contains(
                        query) if partial_match else DirectorModel.normalized_name == query
                )

            if "genre" in search_criteria:
                query = (
                    normalize_name(search_criteria["genre"])
                ) if partial_match else (
                    search_criteria["genre"].lower().strip()
                )
                stmt = stmt.join(
                    MovieGenreModel,
                    MovieGenreModel.movie_id == MovieModel.id
                )
                stmt = stmt.join(
                    GenreModel,
                    GenreModel.id == MovieGenreModel.genre_id
                )
                stmt = stmt.filter(
                    GenreModel.normalized_name.contains(query)
                    if partial_match else GenreModel.normalized_name == query
                )

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_certification_by_id(self, certification_id: int) -> Optional[CertificationModel]:
        stmt = select(CertificationModel).where(
            CertificationModel.id == certification_id
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().first()

    async def create_movie(
            self,
            movie_data: MovieCreateSchema,
            genre_ids: List[int],
            director_ids: List[int],
            star_ids: List[int]
    ) -> MovieModel:
        try:
            movie = MovieModel(
                title=movie_data.title,
                year=movie_data.year,
                time=movie_data.time,
                imdb=movie_data.imdb,
                meta_score=movie_data.meta_score,
                gross=movie_data.gross,
                description=movie_data.description,
                price=movie_data.price,
                certification_id=movie_data.certification_id,
            )
            self.db.add(movie)
            await self.db.flush()

            for genre_id in genre_ids:
                movie_genre = MovieGenreModel(
                    movie_id=movie.id,
                    genre_id=genre_id
                )
                self.db.add(movie_genre)
            for director_id in director_ids:
                movie_director = MovieDirectorModel(
                    movie_id=movie.id,
                    director_id=director_id
                )
                self.db.add(movie_director)
            for star_id in star_ids:
                movie_star = MovieStarModel(
                    movie_id=movie.id,
                    star_id=star_id
                )
                self.db.add(movie_star)

            await self.db.flush()
            await self.db.refresh(movie)
            return movie
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Unexpected error: {str(e)}")

    async def update_movie(self, movie_id: int, movie_data: MovieUpdateSchema) -> MovieModel:
        """
        Обновляет существующий фильм.
        
        Args:
            movie_id: ID фильма для обновления
            movie_data: Новые данные фильма
            
        Returns:
            MovieModel: Обновленный фильм
            
        Raises:
            ValueError: Если данные некорректны
        """
        try:
            movie = await self.get_movie_by_id(movie_id)
            if not movie:
                raise ValueError("Movie not found")

            # Обновляем только те поля, которые были предоставлены
            update_data = movie_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field not in ["genre_ids", "director_ids", "star_ids"]:
                    setattr(movie, field, value)

            await self.db.commit()
            await self.db.refresh(movie)
            return movie

        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error updating movie: {str(e)}")

    async def delete_movie(self, movie_id: int) -> None:
        """
        Удаляет фильм.
        
        Args:
            movie_id: ID фильма для удаления
            
        Raises:
            ValueError: Если фильм не найден или произошла ошибка при удалении
        """
        try:
            movie = await self.get_movie_by_id(movie_id)
            if not movie:
                raise ValueError("Movie not found")

            await self.db.delete(movie)
            await self.db.commit()

        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error deleting movie: {str(e)}")
