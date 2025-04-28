from fastapi import HTTPException

from src.database.models.movies import GenreModel
from src.repositories.movies.genres import GenreRepository


class GenreService:
    def __init__(self, genre_repository: GenreRepository):
        self.genre_repository = genre_repository

    async def create_genre(self, name: str) -> GenreModel:
        try:
            genre = await self.genre_repository.create_genre(name)
            await self.genre_repository.db.commit()
            return genre
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_genre(self, genre_id: int) -> None:
        try:
            await self.genre_repository.delete_genre(genre_id)
            await self.genre_repository.db.commit()
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
