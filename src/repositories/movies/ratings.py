from typing import Optional, List, Dict

from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import MovieRatingModel
from src.repositories.base import BaseRepository


class RatingsRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_movie_rating(self, movie_id: int) -> float:
        stmt = (
            select(func.avg(MovieRatingModel.rating).label("average_rating"))
            .where(MovieRatingModel.movie_id == movie_id)
        )
        result = await self.db.execute(stmt)
        avg_rating = result.scalar()
        return float(avg_rating) if avg_rating is not None else 0.0

    async def get_average_ratings(
            self,
            movie_ids: List[int]
    ) -> Dict[int, float]:
        if not movie_ids:
            return {}
        stmt = (
            select(
                MovieRatingModel.movie_id,
                func.avg(MovieRatingModel.rating).label("average_rating")
            )
            .where(MovieRatingModel.movie_id.in_(movie_ids))
            .group_by(MovieRatingModel.movie_id)
        )
        result = await self.db.execute(stmt)
        ratings = {
            row.movie_id: float(row.average_rating) for row in result.all()
        }
        return ratings

    async def get_user_rating(
            self,
            user_id: int,
            movie_id: int
    ) -> Optional[MovieRatingModel]:
        stmt = (
            select(MovieRatingModel)
            .where(
                MovieRatingModel.user_id == user_id,
                MovieRatingModel.movie_id == movie_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_rating(
            self,
            user_id: int,
            movie_id: int,
            rating: int
    ) -> MovieRatingModel:
        try:
            existing_rating = await self.get_user_rating(user_id, movie_id)
            if existing_rating:
                existing_rating.rating = rating
                await self.db.flush()
                await self.db.refresh(existing_rating)
                return existing_rating
            rating_model = MovieRatingModel(
                user_id=user_id,
                movie_id=movie_id,
                rating=rating
            )
            self.db.add(rating_model)
            await self.db.flush()
            await self.db.refresh(rating_model)
            return rating_model
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create or update rating: {str(e)}")

    async def delete_rating(self, user_id: int, movie_id: int) -> None:
        rating = await self.get_user_rating(user_id, movie_id)
        if not rating:
            raise ValueError(
                f"Rating for user_id {user_id} "
                f"and movie_id {movie_id} not found"
            )
        try:
            await self.db.execute(
                delete(MovieRatingModel).where(
                    MovieRatingModel.user_id == user_id,
                    MovieRatingModel.movie_id == movie_id
                )
            )
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete rating: {str(e)}")
