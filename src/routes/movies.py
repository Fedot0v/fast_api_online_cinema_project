from typing import List, Optional, Sequence, Dict
from fastapi import APIRouter, Depends, Query, status, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import UserModel
from src.dependencies.auth import get_current_user, require_permissions
from src.dependencies.movies import (
    get_movie_service,
    get_comment_service,
    get_favorite_service,
    get_rating_service
)
from src.database.session_sqlite import get_db
from src.schemas.accounts import MessageSchema
from src.schemas.movies import (
    MovieDetail,
    MovieQuery,
    CommentResponseSchema,
    CommentCreateSchema,
    RatingResponse,
    RatingCreate,
    MovieCreateSchema,
    FavoriteResponseSchema,
    MovieUpdateSchema,
)
from src.services.movies.comments_service import CommentsService
from src.services.movies.favorites_service import FavoriteService
from src.services.movies.movie_service import MovieService
from src.services.movies.rating_service import RatingService


router = APIRouter(prefix="/movies", tags=["movies"])


@router.post(
    "/",
    response_model=MovieDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
    description=(
        "Create a new movie in the database with details such as title, year, and price. "
        "Requires 'write' permission."
    ),
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        400: {
            "description": (
                "Bad Request - Invalid data or integrity error "
                "(e.g., duplicate movie title)."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_data": {
                            "summary": "Invalid movie data",
                            "value": {"detail": "Invalid movie data provided."}
                        },
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Certification ID not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Certification not found."}
                }
            }
        },
        500: {
            "description": (
                "Internal Server Error - An error occurred during movie creation."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during movie creation."
                    }
                }
            }
        }
    }
)
async def create_movie(
    movie_data: MovieCreateSchema,
    movie_service: MovieService = Depends(get_movie_service)
) -> MovieDetail:
    movie = await movie_service.create_movie(movie_data)
    return MovieDetail.model_validate(movie)


@router.get(
    "/",
    response_model=List[MovieDetail],
    summary="Query movies",
    description="Retrieve a list of movies with filtering, sorting, and search capabilities. Includes average ratings, genres, directors, and stars. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - List of movies with average ratings.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Inception",
                            "year": 2010,
                            "time": 148,
                            "imdb": 8.8,
                            "meta_score": 74.0,
                            "gross": 829895144.0,
                            "description": "A thief who steals corporate secrets...",
                            "price": 9.99,
                            "certification_id": 1,
                            "average_rating": 8.5,
                            "genres": ["Sci-Fi", "Thriller"],
                            "directors": ["Christopher Nolan"],
                            "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid query parameters (e.g., negative skip, invalid sort_by).",
            "content": {
                "application/json": {
                    "examples": {
                        "negative_skip": {
                            "summary": "Negative skip value",
                            "value": {"detail": "Skip cannot be negative"}
                        },
                        "invalid_sort_by": {
                            "summary": "Invalid sort_by attribute",
                            "value": {"detail": "Invalid sort_by attribute: invalid_field"}
                        },
                        "invalid_filters": {
                            "summary": "Invalid filter parameters",
                            "value": {"detail": "Invalid filters: {'invalid_field'}"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred during movie query.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred during movie query."}
                }
            }
        }
    }
)
async def query_movies(
    skip: int = Query(0, ge=0, description="Number of movies to skip"),
    limit: int = Query(10, gt=0, description="Maximum number of movies to return"),
    sort_by: Optional[str] = Query(None, enum=["title", "year", "imdb", "price", "popularity"], description="Field to sort by"),
    sort_order: str = Query("asc", enum=["asc", "desc"], description="Sort order (ascending or descending)"),
    year: Optional[int] = Query(None, description="Filter by exact year"),
    year_min: Optional[int] = Query(None, description="Filter by minimum year"),
    year_max: Optional[int] = Query(None, description="Filter by maximum year"),
    imdb_min: Optional[float] = Query(None, description="Filter by minimum IMDb rating"),
    imdb_max: Optional[float] = Query(None, description="Filter by maximum IMDb rating"),
    price_min: Optional[float] = Query(None, description="Filter by minimum price"),
    price_max: Optional[float] = Query(None, description="Filter by maximum price"),
    title: Optional[str] = Query(None, description="Search by movie title"),
    description: Optional[str] = Query(None, description="Search by movie description"),
    actor: Optional[str] = Query(None, description="Search by actor name"),
    director: Optional[str] = Query(None, description="Search by director name"),
    genre: Optional[str] = Query(None, description="Search by genre name"),
    partial_match: bool = Query(True, description="Allow partial matches in search"),
    service: MovieService = Depends(get_movie_service),
):
    filters = {}
    if year is not None:
        filters["year"] = year
    if year_min is not None:
        filters["year_min"] = year_min
    if year_max is not None:
        filters["year_max"] = year_max
    if imdb_min is not None:
        filters["imdb_min"] = imdb_min
    if imdb_max is not None:
        filters["imdb_max"] = imdb_max
    if price_min is not None:
        filters["price_min"] = price_min
    if price_max is not None:
        filters["price_max"] = price_max

    search_criteria = {}
    if title:
        search_criteria["title"] = title
    if description:
        search_criteria["description"] = description
    if actor:
        search_criteria["actor"] = actor
    if director:
        search_criteria["director"] = director
    if genre:
        search_criteria["genre"] = genre

    query = MovieQuery(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters if filters else None,
        search_criteria=search_criteria if search_criteria else None,
        partial_match=partial_match
    )
    return await service.query_movies(query)

@router.get(
    "/{movie_id}",
    response_model=MovieDetail,
    summary="Get movie details",
    description="Retrieve detailed information about a specific movie, including its average rating, genres, directors, and stars. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - Movie details with average rating.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Inception",
                        "year": 2010,
                        "time": 148,
                        "imdb": 8.8,
                        "meta_score": 74.0,
                        "gross": 829895144.0,
                        "description": "A thief who steals corporate secrets...",
                        "price": 9.99,
                        "certification_id": 1,
                        "average_rating": 8.5,
                        "genres": ["Sci-Fi", "Thriller"],
                        "directors": ["Christopher Nolan"],
                        "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid movie ID (e.g., negative or zero).",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid movie ID"}
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving movie details.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving movie details."}
                }
            }
        }
    }
)
async def get_movie(
    movie_id: int,
    movie_service: MovieService = Depends(get_movie_service)
) -> MovieDetail:
    return await movie_service.get_movie_detail(movie_id)

@router.get(
    "/{movie_id}/comments",
    response_model=List[CommentResponseSchema],
    summary="Get movie comments",
    description="Retrieve a list of comments for a specific movie, including replies. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - List of comments for the movie.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "movie_id": 1,
                            "user_id": 1,
                            "content": "Great movie!",
                            "created_at": "2025-04-28T12:00:00Z",
                            "replies": []
                        }
                    ]
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving comments.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving comments."}
                }
            }
        }
    }
)
async def get_movie_comments(
    movie_id: int,
    service: CommentsService = Depends(get_comment_service),
) -> List[CommentResponseSchema]:
    return await service.get_movie_comments(movie_id)

@router.post(
    "/{movie_id}/comments",
    response_model=CommentResponseSchema,
    summary="Create a comment",
    description="Add a comment or reply to a movie. Requires 'comment' permission.",
    dependencies=[Depends(require_permissions(["comment"]))],
    responses={
        200: {
            "description": "Successful Response - Comment created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "movie_id": 1,
                        "user_id": 1,
                        "content": "Great movie!",
                        "created_at": "2025-04-28T12:00:00Z",
                        "replies": []
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid comment data (e.g., empty content, invalid parent comment).",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_content": {
                            "summary": "Empty comment content",
                            "value": {"detail": "Comment content cannot be empty."}
                        },
                        "invalid_parent": {
                            "summary": "Invalid parent comment",
                            "value": {"detail": "Parent comment not found."}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while creating the comment.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the comment."}
                }
            }
        }
    }
)
async def create_comment(
    movie_id: int,
    comment_data: CommentCreateSchema,
    current_user: dict = Depends(get_current_user),
    service: CommentsService = Depends(get_comment_service)
) -> CommentResponseSchema:
    comment = await service.create_comment(
        movie_id=movie_id,
        user_id=current_user["user_id"],
        comment_data=comment_data
    )
    return CommentResponseSchema.model_validate(comment)


@router.delete(
    "/{movie_id}/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageSchema,
    summary="Delete a comment",
    description="Delete a comment for a movie. Requires 'delete' permission and ownership, or admin privileges.",
    dependencies=[Depends(require_permissions(["delete"]))],
    responses={
        200: {
            "description": "Successful Response - Comment deleted successfully.",
            "content": {
                "application/json": {
                    "example": {"message": "Comment deleted successfully"}
                }
            }
        },
        404: {
            "description": "Not Found - Movie or comment not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "movie_not_found": {
                            "summary": "Movie not found",
                            "value": {"detail": "Movie not found."}
                        },
                        "comment_not_found": {
                            "summary": "Comment not found",
                            "value": {"detail": "Comment not found."}
                        }
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - User lacks permission to delete the comment.",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to delete this comment."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the comment.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the comment."}
                }
            }
        }
    }
)
async def delete_comment(
    movie_id: int,
    comment_id: int,
    current_user: dict = Depends(get_current_user),
    service: CommentsService = Depends(get_comment_service)
):
    await service.delete_comment(
        movie_id=movie_id,
        comment_id=comment_id,
        user_id=current_user["user_id"],
        user_group=current_user["group_id"]
    )
    return MessageSchema(message="Comment deleted successfully")


@router.get(
    "/my/favorites",
    response_model=List[FavoriteResponseSchema],
    summary="Get user's favorite movies",
    description="Retrieve a list of the user's favorite movies, including average ratings, genres, directors, and stars. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - List of favorite movies with average ratings.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Inception",
                            "year": 2010,
                            "time": 148,
                            "imdb": 8.8,
                            "meta_score": 74.0,
                            "gross": 829895144.0,
                            "description": "A thief who steals corporate secrets...",
                            "price": 9.99,
                            "certification_id": 1,
                            "average_rating": 8.5,
                            "genres": ["Sci-Fi", "Thriller"],
                            "directors": ["Christopher Nolan"],
                            "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving favorites.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving favorites."}
                }
            }
        }
    }
)
async def get_user_favorites(
    user: dict = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
) -> Sequence[FavoriteResponseSchema]:
    favorites = await favorite_service.get_user_favorites(user["user_id"])
    return [FavoriteResponseSchema.model_validate(fav) for fav in favorites]


@router.post(
    "/{movie_id}/favorites",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageSchema,
    summary="Add movie to favorites",
    description="Add a movie to the user's favorites list. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        201: {
            "description": "Successful Response - Movie added to favorites.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie added to favorites"}
                }
            }
        },
        400: {
            "description": "Bad Request - Movie already in favorites or invalid data.",
            "content": {
                "application/json": {
                    "examples": {
                        "already_favorite": {
                            "summary": "Movie already in favorites",
                            "value": {"detail": "Movie already in favorites."}
                        },
                        "invalid_data": {
                            "summary": "Invalid data",
                            "value": {"detail": "Invalid favorite data provided."}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while adding to favorites.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while adding to favorites."}
                }
            }
        }
    }
)
async def add_favorite(
    movie_id: int,
    user: dict = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    await favorite_service.add_favorite(user["user_id"], movie_id)
    return MessageSchema(message="Movie added to favorites")

@router.delete(
    "/{movie_id}/favorites",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove movie from favorites",
    description="Remove a movie from the user's favorites list. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        204: {
            "description": "Successful Response - Movie removed from favorites."
        },
        404: {
            "description": "Not Found - Movie or favorite not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "movie_not_found": {
                            "summary": "Movie not found",
                            "value": {"detail": "Movie not found."}
                        },
                        "favorite_not_found": {
                            "summary": "Favorite not found",
                            "value": {"detail": "Movie not in favorites."}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while removing from favorites.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while removing from favorites."}
                }
            }
        }
    }
)
async def remove_favorite(
    movie_id: int,
    user: dict = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    await favorite_service.remove_favorite(user["user_id"], movie_id)

@router.get(
    "/{movie_id}/favorites/status",
    response_model=bool,
    summary="Check favorite status",
    description="Check if a movie is in the user's favorites list. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - Whether the movie is in favorites.",
            "content": {
                "application/json": {
                    "example": True
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while checking favorite status.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while checking favorite status."}
                }
            }
        }
    }
)
async def check_favorite(
    movie_id: int,
    user: dict = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
) -> bool:
    return await favorite_service.check_favorite(user["user_id"], movie_id)


@router.get(
    "/{movie_id}/ratings",
    response_model=Optional[RatingResponse],
    summary="Get user's rating for a movie",
    description="Retrieve the current user's rating for a specific movie. Returns null if no rating exists. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - User's rating or null if not rated.",
            "content": {
                "application/json": {
                    "examples": {
                        "rating_exists": {
                            "summary": "User has rated the movie",
                            "value": {
                                "rating": 8,
                                "movie_id": 1,
                                "user_id": 1
                            }
                        },
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving the rating.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving the rating."}
                }
            }
        }
    }
)
async def get_user_rating(
    movie_id: int,
    user: dict = Depends(get_current_user),
    rating_service: RatingService = Depends(get_rating_service)
) -> Optional[RatingResponse]:
    rating = await rating_service.get_user_rating(user["user_id"], movie_id)
    if not rating:
        return None
    return RatingResponse(
        rating=rating.rating,
        movie_id=rating.movie_id,
        user_id=rating.user_id
    )

@router.post(
    "/{movie_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update a rating",
    description="Create or update the user's rating for a specific movie (1-10 scale). Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        200: {
            "description": "Successful Response - Rating created or updated.",
            "content": {
                "application/json": {
                    "example": {
                        "rating": 8,
                        "movie_id": 1,
                        "user_id": 1
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid rating (e.g., outside 1-10 range).",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_rating": {
                            "summary": "Invalid rating value",
                            "value": {"detail": "Rating must be between 1 and 10"}
                        },
                        "invalid_data": {
                            "summary": "Invalid rating data",
                            "value": {"detail": "Invalid rating data provided."}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while creating/updating the rating.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating/updating the rating."}
                }
            }
        }
    }
)
async def create_or_update_rating(
    movie_id: int,
    rating_data: RatingCreate,
    user: dict = Depends(get_current_user),
    rating_service: RatingService = Depends(get_rating_service)
) -> RatingResponse:
    rating = await rating_service.create_or_update_rating(user["user_id"], movie_id, rating_data.rating)
    return RatingResponse(
        rating=rating.rating,
        movie_id=rating.movie_id,
        user_id=rating.user_id
    )

@router.delete(
    "/{movie_id}/ratings",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a rating",
    description="Delete the user's rating for a specific movie. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        204: {
            "description": "Successful Response - Rating deleted successfully."
        },
        404: {
            "description": "Not Found - Movie or rating not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "movie_not_found": {
                            "summary": "Movie not found",
                            "value": {"detail": "Movie not found."}
                        },
                        "rating_not_found": {
                            "summary": "Rating not found",
                            "value": {"detail": "Rating not found."}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the rating.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the rating."}
                }
            }
        }
    }
)
async def delete_rating(
    movie_id: int,
    user: dict = Depends(get_current_user),
    rating_service: RatingService = Depends(get_rating_service)
):
    await rating_service.delete_rating(user["user_id"], movie_id)

@router.patch(
    "/{movie_id}",
    response_model=MovieDetail,
    summary="Update a movie",
    description="Update an existing movie's details. Requires 'write' permission.",
    dependencies=[Depends(require_permissions(["write"]))],
    responses={
        200: {
            "description": "Successful Response - Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Updated Movie Title",
                        "year": 2023,
                        "time": 120,
                        "imdb": 8.8,
                        "meta_score": 74.0,
                        "description": "Updated description",
                        "price": 19.99,
                        "certification_id": 1,
                        "average_rating": 8.5,
                        "genres": ["Action", "Drama"],
                        "directors": ["Director Name"],
                        "stars": ["Actor Name"]
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid movie data.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid movie data provided."}
                }
            }
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while updating the movie.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while updating the movie."}
                }
            }
        }
    }
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    movie_service: MovieService = Depends(get_movie_service)
) -> MovieDetail:
    movie = await movie_service.update_movie(movie_id, movie_data)
    return MovieDetail.model_validate(movie)

@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a movie",
    description="Delete a movie. Requires 'delete' permission.",
    dependencies=[Depends(require_permissions(["delete"]))],
    responses={
        204: {
            "description": "Successful Response - Movie deleted successfully."
        },
        404: {
            "description": "Not Found - Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while deleting the movie.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while deleting the movie."}
                }
            }
        }
    }
)
async def delete_movie(
    movie_id: int,
    movie_service: MovieService = Depends(get_movie_service)
):
    await movie_service.delete_movie(movie_id)
