from fastapi import Depends

from src.dependencies.movies import get_repository
from src.repositories.cart.cart_rep import CartRepository
from src.services.cart.cart_service import CartService


def get_cart_service(
        cart_repository: CartRepository = Depends(get_repository(CartRepository))
) -> CartService:
    return CartService(cart_repository)
