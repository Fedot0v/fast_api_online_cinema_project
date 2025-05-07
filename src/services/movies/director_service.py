from fastapi import HTTPException

from src.database.models.movies import DirectorModel
from src.repositories.movies.directors import DirectorRepository


class DirectorService:
    def __init__(self, director_repository: DirectorRepository):
        self.director_repository = director_repository

    async def create_director(self, name: str) -> DirectorModel:
        try:
            star = await self.director_repository.create_director(name)
            await self.director_repository.db.commit()
            return star
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_director(self, star_id: int) -> None:
        try:
            await self.director_repository.delete_director(star_id)
            await self.director_repository.db.commit()
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
