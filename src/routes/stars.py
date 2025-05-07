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
    summary="Create star",
    description="Create a new movie star (actor). Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        201: {
            "description": "Successful Response - Star created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Leonardo DiCaprio"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid star data.",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_name": {
                            "summary": "Empty star name",
                            "value": {"detail": "Star name cannot be empty"}
                        },
                        "duplicate_name": {
                            "summary": "Duplicate star name",
                            "value": {"detail": "Star with this name already exists"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or expired token, or user not active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid token"}
                        },
                        "token_expired": {
                            "summary": "Token expired",
                            "value": {"detail": "Token expired"}
                        },
                        "user_not_active": {
                            "summary": "User not active",
                            "value": {"detail": "User is not active"}
                        }
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - Insufficient permissions.",
            "content": {
                "application/json": {
                    "example": {"detail": "User lacks required permissions"}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while creating the star.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the star."}
                }
            }
        }
    }
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
    summary="Delete star",
    description="Delete a movie star (actor) by ID. Requires 'write' permission. Cannot delete a star if they are associated with any movies.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        204: {
            "description": "Successful Response - Star deleted successfully.",
            "content": {
                "application/json": {
                    "example": {}
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or expired token, or user not active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid token"}
                        },
                        "token_expired": {
                            "summary": "Token expired",
                            "value": {"detail": "Token expired"}
                        },
                        "user_not_active": {
                            "summary": "User not active",
                            "value": {"detail": "User is not active"}
                        }
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - Insufficient permissions.",
            "content": {
                "application/json": {
                    "example": {"detail": "User lacks required permissions"}
                }
            }
        },
        404: {
            "description": "Not Found - Star not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star not found"}
                }
            }
        },
        409: {
            "description": "Conflict - Star cannot be deleted because they are associated with movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot delete star with associated movies"}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the star.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the star."}
                }
            }
        }
    }
)
async def delete_star(
    star_id: int,
    star_service: StarService = Depends(get_star_service)
):
    await star_service.delete_star(star_id)
