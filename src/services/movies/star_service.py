from fastapi import HTTPException

from src.database.models.movies import StarModel
from src.repositories.movies.stars import StarRepository


class StarService:
    def __init__(self, star_repository: StarRepository):
        self.star_repository = star_repository

    async def create_star(self, name: str) -> StarModel:
        try:
            star = await self.star_repository.create_star(name)
            await self.star_repository.db.commit()
            return star
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_star(self, star_id: int) -> None:
        try:
            await self.star_repository.delete_star(star_id)
            await self.star_repository.db.commit()
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
