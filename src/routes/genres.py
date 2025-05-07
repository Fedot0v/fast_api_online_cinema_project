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
    summary="Create genre",
    description="Create a new movie genre. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        201: {
            "description": "Successful Response - Genre created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Sci-Fi"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid genre data.",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_name": {
                            "summary": "Empty genre name",
                            "value": {"detail": "Genre name cannot be empty"}
                        },
                        "duplicate_name": {
                            "summary": "Duplicate genre name",
                            "value": {"detail": "Genre with this name already exists"}
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
            "description": "Internal Server Error - An error occurred while creating the genre.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the genre."}
                }
            }
        }
    }
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
    summary="Delete genre",
    description="Delete a movie genre by ID. Requires 'write' permission. Cannot delete a genre if it is associated with any movies.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        204: {
            "description": "Successful Response - Genre deleted successfully.",
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
            "description": "Not Found - Genre not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre not found"}
                }
            }
        },
        409: {
            "description": "Conflict - Genre cannot be deleted because it is associated with movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot delete genre with associated movies"}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the genre.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the genre."}
                }
            }
        }
    }
)
async def delete_genre(
    genre_id: int,
    genre_service: GenreService = Depends(get_genre_service)
):
    await genre_service.delete_genre(genre_id)
