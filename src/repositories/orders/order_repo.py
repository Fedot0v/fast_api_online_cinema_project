from datetime import datetime
from typing import Any, Type, Coroutine, Sequence, Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.orders import Orders, OrderItems, OrderStatusEnum
from src.exceptions.orders import OrderNotFoundError
from src.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_order(self, order: Orders) -> Orders:
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def _check_order_exists(self, user_id: int, movie_id: int, status: OrderStatusEnum) -> bool:
        stmt = select(OrderItems).join(Orders).where(
            Orders.user_id == user_id,
            OrderItems.movie_id == movie_id,
            Orders.status == status
        )
        result = await self.db.execute(stmt)
        return bool(result.scalars().first())

    async def check_movie_purchased(self, user_id: int, movie_id: int) -> bool:
        return await self._check_order_exists(user_id, movie_id, OrderStatusEnum.PAID)

    async def check_pending_order(self, user_id: int, movie_id: int) -> bool:
        return await self._check_order_exists(user_id, movie_id, OrderStatusEnum.PENDING)

    async def get_order_by_id(self, order_id: int) -> Type[Orders] | None:
        order = await self.db.get(Orders, order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order

    async def update_order_status(
            self,
            order_id: int,
            status: OrderStatusEnum
    ) -> Type[Orders] | None:
        order = await self.get_order_by_id(order_id)
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_orders_by_user_id(self, user_id: int) -> Sequence[Orders]:
        stmt = select(Orders).where(Orders.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_orders_with_filters(
            self,
            user_id: Optional[int] = None,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None,
            status: Optional[OrderStatusEnum] = None
    ) -> Sequence[Orders]:
        query = select(Orders)

        if user_id is not None:
            query = query.where(Orders.user_id == user_id)
        if date_from is not None:
            query = query.where(Orders.created_at >= date_from)
        if date_to is not None:
            query = query.where(Orders.created_at <= date_to)
        if status is not None:
            query = query.where(Orders.status == status)

        result = await self.db.execute(query)
        return result.scalars().all()
