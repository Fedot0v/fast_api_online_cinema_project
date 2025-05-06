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
    summary="Create director",
    description="Create a new director. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        201: {
            "description": "Successful Response - Director created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Christopher Nolan"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid director data.",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_name": {
                            "summary": "Empty director name",
                            "value": {"detail": "Director name cannot be empty"}
                        },
                        "duplicate_name": {
                            "summary": "Duplicate director name",
                            "value": {"detail": "Director with this name already exists"}
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
            "description": "Internal Server Error - An error occurred while creating the director.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the director."}
                }
            }
        }
    }
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
    summary="Delete director",
    description="Delete a director by ID. Requires 'write' permission. Cannot delete a director if they are associated with any movies.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        204: {
            "description": "Successful Response - Director deleted successfully.",
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
            "description": "Not Found - Director not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Director not found"}
                }
            }
        },
        409: {
            "description": "Conflict - Director cannot be deleted because they are associated with movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot delete director with associated movies"}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the director.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the director."}
                }
            }
        }
    }
)
async def delete_director(
    genre_id: int,
    genre_service: DirectorService = Depends(get_director_service)
):
    await genre_service.delete_director(genre_id)
