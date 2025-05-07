from typing import Optional

from fastapi import HTTPException

from src.database.models.movies import MovieRatingModel
from src.repositories.movies.movies import MovieRepository
from src.repositories.movies.ratings import RatingsRepository


class RatingService:
    def __init__(
            self,
            ratings_repository: RatingsRepository,
            movie_repository: MovieRepository
    ):
        self.ratings_repository = ratings_repository
        self.movie_repository = movie_repository

    async def get_user_rating(
            self,
            user_id: int,
            movie_id: int
    ) -> Optional[MovieRatingModel]:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        rating = await self.ratings_repository.get_user_rating(
            user_id,
            movie_id
        )
        return rating

    async def create_or_update_rating(
            self,
            user_id: int,
            movie_id: int,
            rating: int
    ) -> MovieRatingModel:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        try:
            rating_model = await (
                self.ratings_repository.create_or_update_rating(
                    user_id,
                    movie_id,
                    rating
                )
            )
            await self.ratings_repository.db.commit()
            return rating_model
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_rating(self, user_id: int, movie_id: int) -> None:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        try:
            await self.ratings_repository.delete_rating(user_id, movie_id)
            await self.ratings_repository.db.commit()
        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=404,
                    detail="Rating not found"
                )
            raise HTTPException(status_code=400, detail=str(e))
