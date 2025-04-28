from fastapi import Depends, APIRouter, status

from src.dependencies.auth import require_permissions
from src.dependencies.cart import get_cart_service
from src.schemas.cart import CartResponse, CartItemResponse, MovieToCartRequest
from src.services.cart.cart_service import CartService


router = APIRouter(prefix="/cart", tags=["cart"])


@router.post(
    "/add-movie",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to cart",
    description="Add a movie to the user's cart. Creates a cart if it doesn't exist. Ensures the movie is not already in the cart. Requires 'cart' permission and ownership.",
    dependencies=[Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )],
    responses={
        201: {
            "description": "Successful Response - Movie added to cart.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cart_id": 1,
                        "movie_id": 1,
                        "added_at": "2025-04-28T12:00:00Z",
                        "movie": {"id": 1, "title": "Inception", "year": 2010, "price": "9.99"}
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Movie already in cart or cart already exists.",
            "content": {
                "application/json": {
                    "examples": {
                        "already_in_cart": {
                            "summary": "Movie already in cart",
                            "value": {"detail": "Movie with id 1 already in cart"}
                        },
                        "cart_exists": {
                            "summary": "Cart already exists",
                            "value": {"detail": "Cart already exists for user_id 1"}
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
            "description": "Forbidden - Insufficient permissions or not the owner.",
            "content": {
                "application/json": {
                    "examples": {
                        "lacks_permissions": {
                            "summary": "Lacks required permissions",
                            "value": {"detail": "User lacks required permissions"}
                        },
                        "not_owner": {
                            "summary": "Not the owner",
                            "value": {"detail": "User does not have permission to modify this object"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - User, cart, or movie not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "cart_not_found": {
                            "summary": "Cart not found",
                            "value": {"detail": "Cart not found for user_id 1"}
                        },
                        "movie_not_found": {
                            "summary": "Movie not found",
                            "value": {"detail": "Movie with id 1 not found"}
                        },
                        "user_not_found": {
                            "summary": "User not found",
                            "value": {"detail": "User with id 1 not found"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while adding movie to cart.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while adding movie to cart"}
                }
            }
        }
    }
)
async def add_movie_to_cart(
    request: MovieToCartRequest,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )
):
    cart_item = await cart_service.add_movie_to_cart(
        current_user["user_id"],
        request.movie_id
    )
    return CartItemResponse.model_validate(cart_item)

@router.delete(
    "/remove-movie/{movie_id}",
    response_model=CartItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove movie from cart",
    description="Remove a movie from the user's cart. Returns the removed cart item. Requires 'cart' permission and ownership.",
    dependencies=[Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )],
    responses={
        200: {
            "description": "Successful Response - Movie removed from cart.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cart_id": 1,
                        "movie_id": 1,
                        "added_at": "2025-04-28T12:00:00Z",
                        "movie": {"id": 1, "title": "Inception", "year": 2010, "price": "9.99"}
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
            "description": "Forbidden - Insufficient permissions or not the owner.",
            "content": {
                "application/json": {
                    "examples": {
                        "lacks_permissions": {
                            "summary": "Lacks required permissions",
                            "value": {"detail": "User lacks required permissions"}
                        },
                        "not_owner": {
                            "summary": "Not the owner",
                            "value": {"detail": "User does not have permission to modify this object"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Cart or movie not found in cart.",
            "content": {
                "application/json": {
                    "examples": {
                        "cart_not_found": {
                            "summary": "Cart not found",
                            "value": {"detail": "Cart not found for user_id 1"}
                        },
                        "movie_not_found": {
                            "summary": "Movie not found in cart",
                            "value": {"detail": "Movie with id 1 not found in cart"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while removing movie from cart.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while removing movie from cart"}
                }
            }
        }
    }
)
async def remove_movie_from_cart(
    movie_id: int,
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )
):
    cart_item = await cart_service.remove_movie_from_cart(current_user["user_id"], movie_id)
    return CartItemResponse.model_validate(cart_item)

@router.get(
    "/my-cart",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's cart",
    description="Retrieve the user's cart with all items, their associated movies, and total amount to pay. Requires 'cart' permission and ownership.",
    dependencies=[Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )],
    responses={
        200: {
            "description": "Successful Response - Cart retrieved.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "total_amount": "19.98",
                        "cart_items": [
                            {
                                "id": 1,
                                "cart_id": 1,
                                "movie_id": 1,
                                "added_at": "2025-04-28T12:00:00Z",
                                "movie": {"id": 1, "title": "Inception", "year": 2010, "price": "9.99"}
                            },
                            {
                                "id": 2,
                                "cart_id": 1,
                                "movie_id": 2,
                                "added_at": "2025-04-28T12:01:00Z",
                                "movie": {"id": 2, "title": "The Matrix", "year": 1999, "price": "9.99"}
                            }
                        ]
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
            "description": "Forbidden - Insufficient permissions or not the owner.",
            "content": {
                "application/json": {
                    "examples": {
                        "lacks_permissions": {
                            "summary": "Lacks required permissions",
                            "value": {"detail": "User lacks required permissions"}
                        },
                        "not_owner": {
                            "summary": "Not the owner",
                            "value": {"detail": "User does not have permission to modify this object"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Cart not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "cart_not_found": {
                            "summary": "Cart not found",
                            "value": {"detail": "Cart not found for user_id 1"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving cart.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving cart"}
                }
            }
        }
    }
)
async def get_my_cart(
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(
        require_permissions(
            ["cart"],
            require_owner=True)
    )
):
    cart = await cart_service.get_cart(current_user["user_id"])
    return CartResponse.model_validate(cart)

@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear user's cart",
    description="Delete the user's cart and all its items. Requires 'cart' permission and ownership.",
    dependencies=[Depends(require_permissions(
        ["cart"],
        require_owner=True)
    )],
    responses={
        204: {
            "description": "Successful Response - Cart cleared."
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
            "description": "Forbidden - Insufficient permissions or not the owner.",
            "content": {
                "application/json": {
                    "examples": {
                        "lacks_permissions": {
                            "summary": "Lacks required permissions",
                            "value": {"detail": "User lacks required permissions"}
                        },
                        "not_owner": {
                            "summary": "Not the owner",
                            "value": {"detail": "User does not have permission to modify this object"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Cart not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "cart_not_found": {
                            "summary": "Cart not found",
                            "value": {"detail": "Cart not found for user_id 1"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while clearing cart.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while clearing cart"}
                }
            }
        }
    }
)
async def clear_cart(
    cart_service: CartService = Depends(get_cart_service),
    current_user: dict = Depends(
        require_permissions(
            ["cart"],
            require_owner=True)
    )
):
    await cart_service.delete_cart(current_user["user_id"])
