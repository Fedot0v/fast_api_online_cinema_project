from fastapi import APIRouter, status, Depends

from src.dependencies.auth import require_permissions
from src.dependencies.movies import get_star_service
from src.schemas.movies import StarResponseSchema, StarBaseSchema
from src.services.movies.star_service import StarService


router = APIRouter(prefix="/stars", tags=["stars"])


@router.post(
    "/",
    response_model=StarResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def create_star(
    star_data: StarBaseSchema,
    star_service: StarService = Depends(get_star_service)
) -> StarResponseSchema:
    star = await star_service.create_star(star_data.name)
    return StarResponseSchema(id=star.id, name=star.name)


@router.delete(
    "/{star_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(["write"]))],
)
async def delete_star(
    star_id: int,
    star_service: StarService = Depends(get_star_service)
):
    await star_service.delete_star(star_id)
