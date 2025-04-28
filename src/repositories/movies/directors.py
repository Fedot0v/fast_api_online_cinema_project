from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.models.movies import DirectorModel
from src.repositories.base import BaseRepository


class DirectorRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_director_by_id(self, director_id: int) -> Optional[DirectorModel]:
        stmt = select(DirectorModel).where(DirectorModel.id == director_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_director(self, name: str) -> DirectorModel:
        try:
            director = DirectorModel(name=name)
            self.db.add(director)
            await self.db.flush()
            await self.db.refresh(director)
            return director
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create director: {str(e)}")

    async def delete_director(self, director_id: int) -> None:
        director = await self.get_director_by_id(director_id)
        if not director:
            raise ValueError(f"Director with id {director_id} not found")
        try:
            await self.db.delete(director)
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete director: {str(e)}")
