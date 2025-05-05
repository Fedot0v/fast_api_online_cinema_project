from datetime import datetime
from decimal import Decimal
from typing import Tuple, List, Any, Coroutine, Type, Optional, Sequence

from fastapi import HTTPException

from src.database.models.orders import Orders, OrderStatusEnum, OrderItems
from src.exceptions.orders import OrderNotFoundError
from src.repositories.cart.cart_rep import CartRepository
from src.repositories.orders.order_repo import OrderRepository


class OrdersService:
    def __init__(
            self,
            order_repository: OrderRepository,
            cart_repository: CartRepository
    ):
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    async def create_order(
            self,
            user_id: int
    ) -> tuple[Orders, list[Any]]:
        cart = await self.cart_repository.get_by_user_id(user_id)
        if not cart:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty."
            )

        valid_items = []
        exclude_movie_ids = []

        for item in cart.cart_items:
            movie = item.movie
            if await self.order_repository.check_movie_purchased(
                    user_id=user_id,
                    movie_id=movie.id
            ):
                exclude_movie_ids.append(movie.id)
                continue
            if await self.order_repository.check_pending_order(
                    user_id=user_id,
                    movie_id=movie.id
            ):
                exclude_movie_ids.append(movie.id)
                continue
            valid_items.append(item)

        if not valid_items:
            raise HTTPException(
                status_code=400,
                detail="No valid items in cart."
            )

        total_amount = Decimal(sum(item.movie.price for item in valid_items))

        order = Orders(
            user_id=user_id,
            total_amount=total_amount,
            status=OrderStatusEnum.PENDING,
            created_at=datetime.now()
        )
        order.order_items = [
            OrderItems(
                movie_id=item.movie_id,
                price_at_order=item.movie.price
            )
            for item in valid_items
        ]

        order = await self.order_repository.create_order(order)

        await self.cart_repository.delete(user_id)

        return order, exclude_movie_ids

    async def complete_order(
            self,
            order_id: int,
            payment_success: bool
    ) -> Type[Orders] | None:
        try:
            order = await self.order_repository.get_order_by_id(order_id)
        except OrderNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
        if order.status != OrderStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Order cannot be paid"
            )

        new_status = (
            OrderStatusEnum.PAID
        ) if payment_success else OrderStatusEnum.CANCELED
        order = await self.order_repository.update_order_status(
            order_id,
            new_status
        )

        return order

    async def cancel_order(
            self,
            order_id: int,
            user_id: int
    ) -> Type[Orders] | None:
        try:
            order = await self.order_repository.get_order_by_id(order_id)
        except OrderNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if order.status != OrderStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Order cannot be canceled"
            )

        order = await self.order_repository.update_order_status(
            order_id,
            OrderStatusEnum.CANCELED
        )
        return order

    async def get_user_orders(self, user_id: int) -> Sequence[Orders]:
        return await self.order_repository.get_orders_by_user_id(
            user_id
        )


class AdminOrdersService(OrdersService):
    def __init__(
            self,
            order_repository: OrderRepository,
            cart_repository: CartRepository
    ):
        super().__init__(order_repository, cart_repository)

    async def get_all_orders(
            self,
            user_id: Optional[int] = None,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None,
            status: Optional[OrderStatusEnum] = None
    ) -> Sequence[Orders]:
        try:
            orders = await self.order_repository.get_orders_with_filters(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                status=status
            )
            return orders
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")
