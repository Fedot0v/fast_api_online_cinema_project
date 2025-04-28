from fastapi import APIRouter, status, Depends

from src.dependencies.auth import require_permissions
from src.dependencies.movies import get_genre_service
from src.schemas.movies import GenreResponseSchema, GenreBaseSchema
from src.services.movies.genre_service import GenreService


router = APIRouter(prefix="/genres", tags=["genres"])


@router.post(
    "/",
    response_model=GenreResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def create_genre(
    genre_data: GenreBaseSchema,
    genre_service: GenreService = Depends(get_genre_service)
) -> GenreResponseSchema:
    genre = await genre_service.create_genre(genre_data.name)
    return GenreResponseSchema(id=genre.id, name=genre.name)

@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def delete_genre(
    genre_id: int,
    genre_service: GenreService = Depends(get_genre_service)
):
    await genre_service.delete_genre(genre_id)
