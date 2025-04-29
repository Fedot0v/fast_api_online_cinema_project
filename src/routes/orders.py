from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models.orders import StatusEnum
from src.dependencies.auth import require_permissions, get_current_user
from src.dependencies.orders import get_orders_service, get_admin_orders_service
from src.schemas.orders import OrderCreateResponse
from src.services.orders.orders_service import OrdersService, AdminOrdersService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderCreateResponse,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def create_order(
        order_service: OrdersService = Depends(get_orders_service),
):
    current_user = await get_current_user()
    order, excluded_movie_ids = await order_service.create_order(
        current_user["user_id"]
    )

    return OrderCreateResponse(
        id=order.id,
        user_id=order.user_id,
        created_at=order.created_at,
        status=order.status,
        total_amount=order.total_amount,
        order_items=[
            {"movie_id": item.movie_id, "price_at_order": item.price_at_order}
            for item in order.order_items
        ],
        excluded_movie_ids=excluded_movie_ids
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderCreateResponse,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def cancel_order(
        order_id: int,
        order_service: OrdersService = Depends(get_orders_service),
):
    current_user = await get_current_user()

    order = await order_service.cancel_order(order_id, current_user["user_id"])

    return OrderCreateResponse(
        id=order.id,
        user_id=order.user_id,
        created_at=order.created_at,
        status=order.status,
        total_amount=order.total_amount,
        order_items=[
            {"movie_id": item.movie_id, "price_at_order": item.price_at_order}
            for item in order.order_items
        ],
        excluded_movie_ids=[]
    )


@router.get(
    "/admin",
    response_model=List[OrderCreateResponse],
    dependencies=[Depends(require_permissions(["admin"]))]
)
async def get_all_orders(
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[StatusEnum] = None,
        admin_service: AdminOrdersService = Depends(get_admin_orders_service),
):
    orders = await admin_service.get_all_orders(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )

    return [
        OrderCreateResponse(
            id=order.id,
            user_id=order.user_id,
            created_at=order.created_at,
            status=order.status,
            total_amount=order.total_amount,
            order_items=[
                {"movie_id": item.movie_id, "price_at_order": item.price_at_order}
                for item in order.order_items
            ],
            excluded_movie_ids=[]
        )
        for order in orders
    ]
