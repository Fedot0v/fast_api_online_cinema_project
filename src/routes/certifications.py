from fastapi import APIRouter, status, Depends

from src.dependencies.auth import require_permissions
from src.dependencies.movies import get_repository
from src.repositories.movies.certificates import CertificationRepository
from src.schemas.movies import CertificationOutSchema, CertificationCreateSchema


router = APIRouter(prefix="/certifications", tags=["Certifications"])


@router.post(
    "/",
    response_model=CertificationOutSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(["write"]))]
)
async def create_certification_endpoint(
    data: CertificationCreateSchema,
    certification_repo: CertificationRepository = Depends(get_repository(CertificationRepository)),
) -> CertificationOutSchema:
    certification = await certification_repo.create_certification(data.name)
    return CertificationOutSchema.model_validate(certification)


@router.delete(
    "/{certification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(["write"]))]
)
async def delete_certification_endpoint(
    certification_id: int,
    certification_repo: CertificationRepository = Depends(get_repository(CertificationRepository)),
):
    await certification_repo.delete_certification(certification_id)