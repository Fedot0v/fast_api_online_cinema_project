from typing import Sequence

from fastapi import HTTPException

from src.database.models.movies import MovieFavoriteModel, MovieModel
from src.database.models.notifications import NotificationType
from src.repositories.movies.favorites import FavoriteRepository
from src.repositories.movies.movies import MovieRepository
from src.repositories.notifications import NotificationRepository


class FavoriteService:
    def __init__(
            self,
            favorite_repository: FavoriteRepository,
            movie_repository: MovieRepository,
            notification_repository: NotificationRepository
    ):
        self.favorite_repository = favorite_repository
        self.movie_repository = movie_repository
        self.notification_repository = notification_repository

    async def add_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> MovieFavoriteModel:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        try:
            favorite = await self.favorite_repository.add_favorite(
                user_id,
                movie_id
            )
            await self.favorite_repository.db.commit()
            await self.notification_repository.create_notification(
                user_id,
                NotificationType.FAVORITE_ADDED
            )
            return favorite
        except ValueError as e:
            if "unique_user_movie_favorite" in str(e).lower():
                raise HTTPException(
                    status_code=400,
                    detail="Movie already in favorites"
                )
            raise HTTPException(status_code=400, detail=str(e))

    async def remove_favorite(
            self,
            user_id: int,
            movie_id: int
    ) -> None:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(
                status_code=404,
                detail="Movie not found"
            )

        try:
            await self.favorite_repository.remove_favorite(user_id, movie_id)
            await self.favorite_repository.db.commit()
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(
                    status_code=404,
                    detail="Favorite not found"
                )
            raise HTTPException(status_code=400, detail=str(e))

    async def get_user_favorites(self, user_id: int) -> Sequence[MovieModel]:
        favorites = await self.favorite_repository.get_user_favorites(user_id)
        return favorites

    async def check_favorite(self, user_id: int, movie_id: int) -> bool:
        movie = await self.movie_repository.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        favorite = await self.favorite_repository.get_favorite(
            user_id,
            movie_id
        )
        return favorite is not None
