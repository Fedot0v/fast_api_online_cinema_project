from decimal import Decimal

from fastapi import HTTPException

from src.database.models.cart import CartModel, CartItemsModel
from src.exceptions.cart import CartNotFoundError, UserNotFoundError, MovieNotFoundError, CartAlreadyExistsError, \
    MovieAlreadyInCartError, MovieNotInCartError
from src.repositories.cart.cart_rep import CartRepository


class CartService:
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    async def add_movie_to_cart(
            self,
            user_id: int,
            movie_id: int
    ) -> CartItemsModel:
        try:
            return await self.cart_repository.add_movie(user_id, movie_id)
        except CartNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except UserNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except MovieNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except CartAlreadyExistsError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except MovieAlreadyInCartError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while adding movie to cart"
            )

    async def get_cart(self, user_id: int) -> CartModel:
        try:
            cart = await self.cart_repository.get_by_user_id(user_id)
            cart.total_amount = (
                sum(item.movie.price for item in cart.cart_items)
            ) if cart.cart_items else Decimal('0.00')
            return cart
        except CartNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while retrieving cart"
            )

    async def delete_cart(self, user_id: int) -> None:
        try:
            await self.cart_repository.delete(user_id)
        except CartNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while deleting cart"
            )

    async def remove_movie_from_cart(
            self,
            user_id: int,
            movie_id: int
    ) -> CartItemsModel:
        try:
            return await self.cart_repository.remove_movie(user_id, movie_id)
        except CartNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except MovieNotInCartError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while removing movie from cart"
            )
