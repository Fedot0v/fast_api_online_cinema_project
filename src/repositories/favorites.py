from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movies import MovieFavoriteModel, MovieModel
from src.repositories.base import BaseRepository


class FavoritesRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_user_favorites_movies(
            self,
            user_id: int
    ) -> Sequence[MovieModel]:
        stmt = (
            select(MovieModel)
            .join(
                MovieFavoriteModel,
                MovieFavoriteModel.movie_id == MovieModel.id
            )
            .where(MovieFavoriteModel.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> Optional[MovieFavoriteModel]:
        stmt = select(MovieFavoriteModel).where(
            MovieFavoriteModel.user_id == user_id,
            MovieFavoriteModel.movie_id == movie_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def toggle_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> MovieFavoriteModel:
        existing_favorite = await self.get_favorite(user_id, movie_id)
        if existing_favorite:
            await self.db.delte(existing_favorite)
            await self.db.commit()
            return existing_favorite
        favorite = MovieFavoriteModel(
            user_id=user_id,
            movie_id=movie_id
        )
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite
