from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends

from src.database.models.orders import OrderStatusEnum
from src.dependencies.auth import require_permissions, get_current_user
from src.dependencies.orders import get_orders_service, get_admin_orders_service
from src.dependencies.payments import get_payment_service
from src.schemas.accounts import MessageSchema
from src.schemas.orders import OrderCreateResponse, OrderItemResponse
from src.schemas.payments import PaymentResponse, PaymentDetailResponse, RefundRequest
from src.services.auth.user_auth_service import UserAuthService
from src.services.orders.orders_service import OrdersService, AdminOrdersService
from src.services.payments.payments_service import PaymentService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderCreateResponse,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def create_order(
        order_service: OrdersService = Depends(get_orders_service),
        current_user: dict = Depends(get_current_user),
):
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
                OrderItemResponse(
                    movie_id=item.movie_id,
                    price_at_order=item.price_at_order
                )
                for item in order.order_items
            ],
            excluded_movie_ids=excluded_movie_ids
        )


@router.post(
    "/{order_id}/cancel",
    response_model=MessageSchema,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def cancel_order(
        order_id: int,
        current_user: dict = Depends(get_current_user),
        order_service: OrdersService = Depends(get_orders_service),
):

    await order_service.cancel_order(order_id, current_user["user_id"])

    return MessageSchema(message="Your order is successfully canceled.")


@router.get(
    "/admin",
    response_model=List[OrderCreateResponse],
    dependencies=[Depends(require_permissions(["admin"]))]
)
async def get_all_orders(
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[OrderStatusEnum] = None,
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
                OrderItemResponse(
                    movie_id=item.movie_id,
                    price_at_order=item.price_at_order
                )
                for item in order.order_items
            ],
            excluded_movie_ids=[]
        )
        for order in orders
    ]


@router.post(
    "/{order_id}/pay",
    response_model=PaymentResponse,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def initiate_payment(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    client_secret = await payment_service.initiate_payment(
        order_id,
        current_user["user_id"]
    )
    return PaymentResponse(client_secret=client_secret)

@router.post(
    "/{order_id}/refund",
    response_model=PaymentDetailResponse,
    dependencies=[Depends(require_permissions(["read"]))]
)
async def refund_payment(
    order_id: int,
    request: RefundRequest,
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payment = await payment_service.refund_payment(
        order_id=order_id,
        user_id=current_user["user_id"],
        amount=request.amount
    )
    return PaymentDetailResponse.from_orm(payment)

@router.get(
    "/payments",
    response_model=List[PaymentDetailResponse],
    dependencies=[Depends(require_permissions(["read"]))]
)
async def get_user_payments(
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payments = await payment_service.get_user_payments(current_user["user_id"])
    return [PaymentDetailResponse.model_validate(payment) for payment in payments]

@router.get(
    "/{order_id}/payments",
    response_model=List[PaymentDetailResponse],
    dependencies=[Depends(require_permissions(["read"]))]
)
async def get_order_payments(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payments = await payment_service.get_order_payments(
        order_id,
        current_user["user_id"]
    )
    return [PaymentDetailResponse.model_validate(payment) for payment in payments]


@router.post("/webhooks/payment")
async def handle_payment_webhook(
    payload: dict,
    payment_service: PaymentService = Depends(get_payment_service),
):
    payment = await payment_service.complete_payment(
        payload.get("external_payment_id")
    )
    return {"status": "success", "payment_id": payment.id}
