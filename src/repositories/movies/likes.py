from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import MovieLikeModel
from src.repositories.base import BaseRepository


class LikeRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_movie_like(self, user_id: int, movie_id: int) -> Optional[MovieLikeModel]:
        stmt = select(MovieLikeModel).where(
            MovieLikeModel.user_id == user_id,
            MovieLikeModel.movie_id == movie_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def toggle_movie_like(
            self,
            user_id: int,
            movie_id: int,
    ) -> MovieLikeModel:
        existing_like = await self.get_movie_like(user_id, movie_id)
        if existing_like:
            existing_like.is_like = not existing_like.is_like
            await self.db.commit()
            await self.db.refresh(existing_like)
            return existing_like
        like = MovieLikeModel(
            user_id=user_id,
            movie_id=movie_id,
            is_like=True
        )
        self.db.add(like)
        await self.db.commit()
        await self.db.refresh(like)
        return like