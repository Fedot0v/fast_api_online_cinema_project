from typing import List, Any, Coroutine, Sequence, Optional, Dict

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import MovieModel, MovieGenreModel, GenreModel, MovieStarModel, StarModel, \
    MovieDirectorModel, DirectorModel
from src.database.utils import normalize_name
from src.repositories.base import BaseRepository


class MovieRepository(BaseRepository):
    def __init__(
            self,
            db: AsyncSession
    ):
        super().__init__(db)

    async def get_movies(
            self,
            skip: int = 0,
            limit: int = 10,
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ) -> Sequence[MovieModel]:
        stmt = select(MovieModel)
        if sort_by:
            sort_attr = getattr(MovieModel, sort_by, None)
            if sort_attr is None:
                raise ValueError(f"Invalid sort_by attribute: {sort_by}")
            stmt = stmt.order_by(asc(sort_attr) if sort_order == "asc" else desc(sort_attr))
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_movie_by_id(self, movie_id: int) -> MovieModel:
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def filter_movies(
            self,
            filters: Dict[str, any] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "asc",
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> Sequence[MovieModel]:
        stmt = select(MovieModel)
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
            stmt = stmt.order_by(asc(sort_attr) if sort_order == "asc" else desc(sort_attr))
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_movies(
            self,
            search_criteria: Dict[str, str] = None,
            partial_match: bool = True,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> Sequence[MovieModel]:
        """
        Search movies by multiple criteria (title, description, actor, director, genre).

        Args:
            search_criteria: Dict with search criteria (e.g., {"actor": "Tom Cruise", "director": "Christopher Nolan"}).
                             Supported keys: "title", "description", "actor", "director", "genre".
            partial_match: If True, use partial matching (contains); otherwise, exact matching.
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).

        Returns:
            Sequence of MovieModel objects.
        """
        stmt = select(MovieModel).distinct()

        if search_criteria:
            valid_criteria = {"title", "description", "actor", "director", "genre"}
            invalid_criteria = set(search_criteria) - valid_criteria
            if invalid_criteria:
                raise ValueError(f"Invalid search criteria: {invalid_criteria}")

            if "title" in search_criteria:
                query = normalize_name(search_criteria["title"]) if partial_match else search_criteria[
                    "title"].lower().strip()
                stmt = stmt.filter(
                    MovieModel.title.contains(query) if partial_match else MovieModel.title.ilike(query)
                )

            if "description" in search_criteria:
                query = normalize_name(search_criteria["description"]) if partial_match else search_criteria[
                    "description"].lower().strip()
                stmt = stmt.filter(
                    MovieModel.description.contains(query) if partial_match else MovieModel.description.ilike(query)
                )

            if "actor" in search_criteria:
                query = normalize_name(search_criteria["actor"]) if partial_match else search_criteria[
                    "actor"].lower().strip()
                stmt = stmt.join(MovieStarModel, MovieStarModel.movie_id == MovieModel.id)
                stmt = stmt.join(StarModel, StarModel.id == MovieStarModel.star_id)
                stmt = stmt.filter(
                    StarModel.normalized_name.contains(query) if partial_match else StarModel.normalized_name == query
                )

            if "director" in search_criteria:
                query = normalize_name(search_criteria["director"]) if partial_match else search_criteria[
                    "director"].lower().strip()
                stmt = stmt.join(MovieDirectorModel, MovieDirectorModel.movie_id == MovieModel.id)
                stmt = stmt.join(DirectorModel, DirectorModel.id == MovieDirectorModel.director_id)
                stmt = stmt.filter(
                    DirectorModel.normalized_name.contains(
                        query) if partial_match else DirectorModel.normalized_name == query
                )

            if "genre" in search_criteria:
                query = normalize_name(search_criteria["genre"]) if partial_match else search_criteria[
                    "genre"].lower().strip()
                stmt = stmt.join(MovieGenreModel, MovieGenreModel.movie_id == MovieModel.id)
                stmt = stmt.join(GenreModel, GenreModel.id == MovieGenreModel.genre_id)
                stmt = stmt.filter(
                    GenreModel.normalized_name.contains(query) if partial_match else GenreModel.normalized_name == query
                )

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()
