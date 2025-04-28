from fastapi import APIRouter, status, Depends

from src.dependencies.auth import require_permissions
from src.dependencies.movies import get_director_service
from src.schemas.movies import DirectorBaseSchema, GenreResponseSchema
from src.services.movies.director_service import DirectorService


router = APIRouter(prefix="/directors", tags=["directors"])


@router.post(
    "/",
    response_model=DirectorBaseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def create_director(
    genre_data: DirectorBaseSchema,
    genre_service: DirectorService = Depends(get_director_service)
) -> GenreResponseSchema:
    genre = await genre_service.create_director(genre_data.name)
    return GenreResponseSchema(id=genre.id, name=genre.name)


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def delete_director(
    genre_id: int,
    genre_service: DirectorService = Depends(get_director_service)
):
    await genre_service.delete_director(genre_id)
