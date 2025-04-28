from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


from src.database.models.movies import GenreModel
from src.repositories.base import BaseRepository


class GenreRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_genre_by_id(self, genre_id: int) -> Optional[GenreModel]:
        stmt = select(GenreModel).where(GenreModel.id == genre_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_genre(self, name: str) -> GenreModel:
        try:
            genre = GenreModel(name=name)
            self.db.add(genre)
            await self.db.flush()
            await self.db.refresh(genre)
            return genre
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create genre: {str(e)}")

    async def delete_genre(self, genre_id: int) -> None:
        genre = await self.get_genre_by_id(genre_id)
        if not genre:
            raise ValueError(f"Genre with id {genre_id} not found")
        try:
            await self.db.delete(genre)
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete genre: {str(e)}")
