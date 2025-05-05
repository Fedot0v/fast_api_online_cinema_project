from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.models.movies import CertificationModel
from src.repositories.base import BaseRepository


class CertificationRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_certification_by_id(self, certification_id: int) -> Optional[CertificationModel]:
        stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_certification(self, name: str) -> CertificationModel:
        certification = CertificationModel(name=name)
        self.db.add(certification)
        await self.db.commit()
        await self.db.refresh(certification)
        return certification

    async def delete_certification(self, certification_id: int) -> None:
        stmt = delete(CertificationModel).where(CertificationModel.id == certification_id)
        await self.db.execute(stmt)
        await self.db.commit()