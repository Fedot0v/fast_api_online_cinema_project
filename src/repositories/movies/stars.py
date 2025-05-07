from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.models.movies import StarModel
from src.repositories.base import BaseRepository


class StarRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_star_by_id(self, star_id: int) -> Optional[StarModel]:
        stmt = select(StarModel).where(StarModel.id == star_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_star(self, name: str) -> StarModel:
        try:
            star = StarModel(name=name)
            self.db.add(star)
            await self.db.flush()
            await self.db.refresh(star)
            return star
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create star: {str(e)}")

    async def delete_star(self, star_id: int) -> None:
        star = await self.get_star_by_id(star_id)
        if not star:
            raise ValueError(f"Star with id {star_id} not found")
        try:
            await self.db.delete(star)
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete star: {str(e)}")
