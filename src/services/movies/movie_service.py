from typing import Optional, List, Sequence
from fastapi import HTTPException
from src.database.models.movies import MovieModel
from src.repositories.movies.certificates import CertificationRepository
from src.repositories.movies.directors import DirectorRepository
from src.repositories.movies.genres import GenreRepository
from src.repositories.movies.movies import MovieRepository
from src.repositories.movies.ratings import RatingsRepository
from src.repositories.movies.stars import StarRepository
from src.schemas.movies import MovieBase, MovieDetail, MovieQuery

class MovieService:
    def __init__(
            self,
            movie_repository: MovieRepository,
            genre_repository: GenreRepository,
            star_repository: StarRepository,
            director_repository: DirectorRepository,
            certification_repository: CertificationRepository,
            ratings_repository: RatingsRepository,
    ):
        self.movie_repository = movie_repository
        self.genre_repository = genre_repository
        self.star_repository = star_repository
        self.director_repository = director_repository
        self.certification_repository = certification_repository
        self.ratings_repository = ratings_repository

    @staticmethod
    async def _validate_pagination(skip: int, limit: int) -> None:
        if skip < 0:
            raise HTTPException(status_code=400, detail="Skip cannot be negative.")
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit must be greater than zero.")

    @staticmethod
    async def _validate_sort(sort_by: Optional[str], sort_order: Optional[str]) -> None:
        if sort_by and sort_by not in {"title", "year", "imdb", "price", "popularity"}:
            raise HTTPException(status_code=400, detail=f"Invalid sort_by attribute: {sort_by}")
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")

    @staticmethod
    async def _validate_filters(filters: Optional[dict]) -> None:
        if filters:
            valid_filters = {"year", "year_min", "year_max", "imdb_min", "imdb_max", "price_min", "price_max"}
            invalid_filters = set(filters) - valid_filters
            if invalid_filters:
                raise HTTPException(status_code=400, detail=f"Invalid filters: {invalid_filters}")
            if "year" in filters and not isinstance(filters["year"], int):
                raise HTTPException(status_code=400, detail="Year must be an integer")
            for key in ["year_min", "year_max"]:
                if key in filters and not isinstance(filters[key], int):
                    raise HTTPException(status_code=400, detail=f"{key} must be an integer")
            for key in ["imdb_min", "imdb_max", "price_min", "price_max"]:
                if key in filters and not isinstance(filters[key], (int, float)):
                    raise HTTPException(status_code=400, detail=f"{key} must be a number")
            if "year_min" in filters and "year_max" in filters and filters["year_min"] > filters["year_max"]:
                raise HTTPException(status_code=400, detail="year_min cannot be greater than year_max")
            if "imdb_min" in filters and "imdb_max" in filters and filters["imdb_min"] > filters["imdb_max"]:
                raise HTTPException(status_code=400, detail="imdb_min cannot be greater than imdb_max")
            if "price_min" in filters and "price_max" in filters and filters["price_min"] > filters["price_max"]:
                raise HTTPException(status_code=400, detail="price_min cannot be greater than price_max")

    @staticmethod
    async def _validate_search_criteria(search_criteria: Optional[dict]) -> None:
        if search_criteria:
            valid_criteria = {"title", "description", "actor", "director", "genre"}
            invalid_criteria = set(search_criteria) - valid_criteria
            if invalid_criteria:
                raise HTTPException(status_code=400, detail=f"Invalid search criteria: {invalid_criteria}")
            for key, value in search_criteria.items():
                if not isinstance(value, str):
                    raise HTTPException(status_code=400, detail=f"Search criterion {key} must be a string")
                if not value.strip():
                    raise HTTPException(status_code=400, detail=f"Search criterion {key} cannot be empty")

    async def _enrich_movies_with_ratings(self, movies: Sequence[MovieModel]) -> Sequence[MovieDetail]:
        movie_ids = [movie.id for movie in movies]
        average_ratings = await self.ratings_repository.get_average_ratings(movie_ids)

        result = []
        for movie in movies:
            average_rating = average_ratings.get(movie.id, 0.0)
            result.append(
                MovieDetail(
                    id=movie.id,
                    title=movie.title,
                    year=movie.year,
                    time=movie.time,
                    imdb=movie.imdb,
                    meta_score=movie.meta_score,
                    gross=movie.gross,
                    description=movie.description,
                    price=movie.price,
                    certification_id=movie.certification_id,
                    average_rating=average_rating,
                    genres=[genre.name for genre in movie.genres],
                    directors=[director.name for director in movie.directors],
                    stars=[star.name for star in movie.stars]
                )
            )
        return result

    async def get_movies(
            self,
            skip: int = 0,
            limit: int = 10,
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ) -> Sequence[MovieDetail]:
        await self._validate_pagination(skip, limit)
        await self._validate_sort(sort_by, sort_order)
        try:
            movies = await self.movie_repository.get_movies(skip, limit, sort_by, sort_order)
            return await self._enrich_movies_with_ratings(movies)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def filter_movies(
            self,
            filters: Optional[dict] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "asc",
            limit: Optional[int] = 10,
            offset: Optional[int] = 0
    ) -> Sequence[MovieDetail]:
        await self._validate_pagination(offset, limit)
        await self._validate_sort(sort_by, sort_order)
        await self._validate_filters(filters)
        try:
            movies = await self.movie_repository.filter_movies(filters or {}, sort_by, sort_order, limit, offset)
            return await self._enrich_movies_with_ratings(movies)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def search_movies(
            self,
            search_criteria: Optional[dict] = None,
            partial_match: bool = True,
            limit: Optional[int] = 10,
            offset: Optional[int] = 0
    ) -> Sequence[MovieDetail]:
        await self._validate_pagination(offset, limit)
        await self._validate_search_criteria(search_criteria)
        try:
            movies = await self.movie_repository.search_movies(search_criteria or {}, partial_match, limit, offset)
            return await self._enrich_movies_with_ratings(movies)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_movie_detail(self, movie_id: int) -> MovieDetail:
        if movie_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid movie ID")
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return (await self._enrich_movies_with_ratings([movie]))[0]

    async def query_movies(self, query: MovieQuery) -> Sequence[MovieDetail]:

        if query.skip < 0:
            raise HTTPException(
                status_code=400,
                detail="Skip cannot be negative"
            )
        if query.limit <= 0:
            raise HTTPException(
                status_code=400,
                detail="Limit must be greater than zero"
            )
        if query.sort_by and query.sort_by not in {
            "title",
            "year",
            "imdb",
            "price",
            "popularity"
        }:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by attribute: {query.sort_by}"
            )
        if query.sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400,
                detail="Sort order must be 'asc' or 'desc'"
            )
        if query.filters:
            valid_filters = {
                "year",
                "year_min",
                "year_max",
                "imdb_min",
                "imdb_max",
                "price_min",
                "price_max"
            }
            invalid_filters = set(query.filters) - valid_filters
            if invalid_filters:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filters: {invalid_filters}"
                )

        filters = query.filters or {}
        search_criteria = query.search_criteria or {}

        try:
            if search_criteria and filters:
                search_results = await self.movie_repository.search_movies(
                    search_criteria=search_criteria,
                    partial_match=query.partial_match,
                    limit=None,
                    offset=None
                )
                movie_ids = [movie.id for movie in search_results]
                if not movie_ids:
                    return []
                filters["ids"] = movie_ids
                movies = await self.movie_repository.filter_movies(
                    filters=filters,
                    sort_by=query.sort_by,
                    sort_order=query.sort_order,
                    limit=query.limit,
                    offset=query.skip
                )
            elif search_criteria:
                movies = await self.movie_repository.search_movies(
                    search_criteria=search_criteria,
                    partial_match=query.partial_match,
                    limit=query.limit,
                    offset=query.skip
                )
            elif filters:
                movies = await self.movie_repository.filter_movies(
                    filters=filters,
                    sort_by=query.sort_by,
                    sort_order=query.sort_order,
                    limit=query.limit,
                    offset=query.skip
                )
            else:
                movies = await self.movie_repository.get_movies(
                    skip=query.skip,
                    limit=query.limit,
                    sort_by=query.sort_by,
                    sort_order=query.sort_order
                )
            return await self._enrich_movies_with_ratings(movies)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def create_movie(self, movie_data: MovieBase) -> MovieModel:
        certification = await (
            self.certification_repository
            .get_certification_by_id(movie_data.certification_id)
        )
        if not certification:
            raise HTTPException(
                status_code=404,
                detail="Certification not found"
            )

        genre_ids = movie_data.genre_ids or []
        for genre_id in genre_ids:
            if not await self.genre_repository.get_genre_by_id(genre_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Genre with id {genre_id} not found"
                )

        director_ids = movie_data.director_ids or []
        for director_id in director_ids:
            if not await self.director_repository.get_director_by_id(
                    director_id
            ):
                raise HTTPException(
                    status_code=404,
                    detail=f"Director with id {director_id} not found"
                )

        star_ids = movie_data.star_ids or []
        for star_id in star_ids:
            if not await self.star_repository.get_star_by_id(star_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Star with id {star_id} not found"
                )

        try:
            movie = await (
                self.movie_repository.create_movie(
                    movie_data,
                    genre_ids,
                    director_ids,
                    star_ids
                )
            )
            await self.movie_repository.db.commit()
            return movie
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def enrich_movies(
            self,
            movies: Sequence[MovieModel]
    ) -> Sequence[MovieDetail]:
        return await self._enrich_movies_with_ratings(movies)
