from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi import status

from src.database.models.orders import OrderStatusEnum
from src.dependencies.auth import require_permissions, get_current_user
from src.dependencies.orders import get_orders_service, get_admin_orders_service
from src.dependencies.payments import get_payment_service, get_settings_dependency
from src.schemas.accounts import MessageSchema
from src.schemas.orders import OrderCreateResponse, OrderItemResponse
from src.schemas.payments import PaymentResponse, PaymentDetailResponse, RefundRequest
from src.services.auth.user_auth_service import UserAuthService
from src.services.orders.orders_service import OrdersService, AdminOrdersService
from src.services.payments.payments_service import PaymentService
from src.config.settings import BaseSettings
import stripe

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderCreateResponse,
    status_code=201,
    summary="Create order",
    description="Create a new order from the user's cart. Requires 'read' permission. The cart will be cleared after successful order creation.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        201: {
            "description": "Successful Response - Order created successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "created_at": "2025-04-28T12:00:00Z",
                        "status": "pending",
                        "total_amount": "19.98",
                        "order_items": [
                            {
                                "movie_id": 1,
                                "price_at_order": "9.99"
                            },
                            {
                                "movie_id": 2,
                                "price_at_order": "9.99"
                            }
                        ],
                        "excluded_movie_ids": []
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Cart is empty or no valid items in cart.",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_cart": {
                            "summary": "Cart is empty",
                            "value": {"detail": "Cart is empty."}
                        },
                        "no_valid_items": {
                            "summary": "No valid items in cart",
                            "value": {"detail": "No valid items in cart."}
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
            "description": "Internal Server Error - An error occurred while creating the order.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the order."}
                }
            }
        }
    }
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
    status_code=status.HTTP_200_OK,
    summary="Cancel order",
    description="Cancel a pending order. Only the order owner can cancel their order, and only if it's in PENDING status. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - Order canceled successfully.",
            "content": {
                "application/json": {
                    "example": {"message": "Your order is successfully canceled."}
                }
            }
        },
        400: {
            "description": "Bad Request - Order cannot be canceled (e.g., already paid or canceled).",
            "content": {
                "application/json": {
                    "example": {"detail": "Order cannot be canceled"}
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
            "description": "Forbidden - Not authorized to cancel this order.",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized"}
                }
            }
        },
        404: {
            "description": "Not Found - Order not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while canceling the order.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while canceling the order."}
                }
            }
        }
    }
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
    summary="Get all orders (admin)",
    description="Retrieve a list of all orders with optional filtering by user, date range, and status. Requires 'manage_users' permission.",
    dependencies=[Depends(require_permissions(["manage_users"]))],
    responses={
        200: {
            "description": "Successful Response - List of orders.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "created_at": "2025-04-28T12:00:00Z",
                            "status": "pending",
                            "total_amount": "19.98",
                            "order_items": [
                                {
                                    "movie_id": 1,
                                    "price_at_order": "9.99"
                                }
                            ],
                            "excluded_movie_ids": []
                        }
                    ]
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
            "description": "Forbidden - User lacks admin privileges.",
            "content": {
                "application/json": {
                    "example": {"detail": "User lacks required permissions"}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving orders.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to fetch orders"}
                }
            }
        }
    }
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
    status_code=status.HTTP_200_OK,
    summary="Initiate payment",
    description="Initiate payment for a pending order. Creates a Stripe payment intent and returns the client secret. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - Payment initiated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "client_secret": "pi_1234567890_secret_1234567890"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Order cannot be paid (e.g., not in PENDING status).",
            "content": {
                "application/json": {
                    "example": {"detail": "Order cannot be paid"}
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
            "description": "Forbidden - Not authorized to pay for this order.",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized"}
                }
            }
        },
        404: {
            "description": "Not Found - Order not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while initiating payment.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while initiating payment."}
                }
            }
        }
    }
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
    status_code=status.HTTP_200_OK,
    summary="Refund payment",
    description="Refund a payment for a paid order. Can refund partial or full amount. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - Payment refunded successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "order_id": 1,
                        "amount": "19.98",
                        "status": "refunded",
                        "payment_intent_id": "pi_1234567890",
                        "created_at": "2025-04-28T12:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid refund request (e.g., amount too high, already refunded).",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_amount": {
                            "summary": "Invalid refund amount",
                            "value": {"detail": "Refund amount exceeds payment amount"}
                        },
                        "already_refunded": {
                            "summary": "Already refunded",
                            "value": {"detail": "Payment has already been refunded"}
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
            "description": "Forbidden - Not authorized to refund this payment.",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized"}
                }
            }
        },
        404: {
            "description": "Not Found - Order or payment not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "order_not_found": {
                            "summary": "Order not found",
                            "value": {"detail": "Order not found."}
                        },
                        "payment_not_found": {
                            "summary": "Payment not found",
                            "value": {"detail": "Payment not found."}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while processing refund.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while processing refund."}
                }
            }
        }
    }
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
    status_code=status.HTTP_200_OK,
    summary="Get user payments",
    description="Retrieve a list of all payments made by the current user. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - List of user payments.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "order_id": 1,
                            "amount": "19.98",
                            "status": "succeeded",
                            "payment_intent_id": "pi_1234567890",
                            "created_at": "2025-04-28T12:00:00Z"
                        }
                    ]
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
            "description": "Internal Server Error - An error occurred while retrieving payments.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving payments."}
                }
            }
        }
    }
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
    status_code=status.HTTP_200_OK,
    summary="Get order payments",
    description="Retrieve a list of all payments for a specific order. Only the order owner can view these payments. Requires 'read' permission.",
    dependencies=[Depends(require_permissions(["read"]))],
    responses={
        200: {
            "description": "Successful Response - List of order payments.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "order_id": 1,
                            "amount": "19.98",
                            "status": "succeeded",
                            "payment_intent_id": "pi_1234567890",
                            "created_at": "2025-04-28T12:00:00Z"
                        }
                    ]
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
            "description": "Forbidden - Not authorized to view these payments.",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized"}
                }
            }
        },
        404: {
            "description": "Not Found - Order not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while retrieving payments.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while retrieving payments."}
                }
            }
        }
    }
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


@router.post(
    "/webhooks/payment",
    status_code=status.HTTP_200_OK,
    summary="Payment webhook",
    description="Handle Stripe payment webhook events. Processes payment success and failure events to update order status.",
    responses={
        200: {
            "description": "Successful Response - Webhook event processed.",
            "content": {
                "application/json": {
                    "examples": {
                        "payment_success": {
                            "summary": "Payment succeeded",
                            "value": {
                                "status": "success",
                                "payment_id": 1
                            }
                        },
                        "payment_failed": {
                            "summary": "Payment failed",
                            "value": {
                                "status": "failed",
                                "payment_id": 1,
                                "error": "Your card was declined."
                            }
                        },
                        "ignored": {
                            "summary": "Event ignored",
                            "value": {
                                "status": "ignored"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid payload or signature.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_payload": {
                            "summary": "Invalid payload",
                            "value": {"detail": "Invalid payload"}
                        },
                        "invalid_signature": {
                            "summary": "Invalid signature",
                            "value": {"detail": "Invalid signature"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred while processing the webhook.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while processing the webhook."}
                }
            }
        }
    }
)
async def handle_payment_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
    settings: BaseSettings = Depends(get_settings_dependency),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        payment = await payment_service.complete_payment(payment_intent["id"])
        return {"status": "success", "payment_id": payment.id}
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        error_message = payment_intent.get("last_payment_error", {}).get("message")
        payment = await payment_service.complete_payment(payment_intent["id"])
        return {
            "status": "failed",
            "payment_id": payment.id,
            "error": error_message
        }
    
    return {"status": "ignored"}
