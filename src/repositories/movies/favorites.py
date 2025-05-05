from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import MovieFavoriteModel, MovieModel
from src.repositories.base import BaseRepository


class FavoriteRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def add_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> MovieFavoriteModel:
        try:
            favorite = MovieFavoriteModel(user_id=user_id, movie_id=movie_id)
            self.db.add(favorite)
            await self.db.flush()
            await self.db.refresh(favorite)
            return favorite
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to add favorite: {str(e)}")

    async def remove_favorite(self, user_id: int, movie_id: int) -> None:
        favorite = await self.get_favorite(user_id, movie_id)
        if not favorite:
            raise ValueError(
                f"Favorite with user_id {user_id} "
                f"and movie_id {movie_id} not found"
            )
        try:
            await self.db.delete(favorite)
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to remove favorite: {str(e)}")

    async def toggle_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> tuple[MovieFavoriteModel, bool]:
        existing_favorite = await self.get_favorite(user_id, movie_id)
        if existing_favorite:
            await self.remove_favorite(user_id, movie_id)
            return existing_favorite, False
        favorite = await self.add_favorite(user_id, movie_id)
        return favorite, True

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

    async def get_user_favorites(self, user_id: int) -> Sequence[MovieFavoriteModel]:
        stmt = (
            select(MovieFavoriteModel)
            .options(selectinload(MovieFavoriteModel.movie))
            .where(MovieFavoriteModel.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()