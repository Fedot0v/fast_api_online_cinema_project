from fastapi import Depends

from src.dependencies.movies import get_repository
from src.repositories.cart.cart_rep import CartRepository
from src.repositories.orders.order_repo import OrderRepository
from src.services.orders.orders_service import OrdersService, AdminOrdersService


def get_orders_service(
        order_repository = Depends(get_repository(OrderRepository)),
        cart_repository = Depends(get_repository(CartRepository))
) -> OrdersService:
    return OrdersService(order_repository, cart_repository)


def get_admin_orders_service(
        order_repository = Depends(get_repository(OrderRepository)),
        cart_repository = Depends(get_repository(CartRepository))
) -> AdminOrdersService:
    return AdminOrdersService(order_repository, cart_repository)