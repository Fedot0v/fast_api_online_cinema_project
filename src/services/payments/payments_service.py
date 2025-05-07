from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence

from fastapi import HTTPException

from src.database.models.orders import OrderStatusEnum
from src.database.models.payments import Payment, PaymentStatusEnum, PaymentItem
from src.providers.payment_provider import PaymentProviderInterface
from src.repositories.cart.cart_rep import CartRepository
from src.repositories.orders.order_repo import OrderRepository
from src.repositories.payments.payments_repo import PaymentsRepository
from src.exceptions.orders import OrderNotFoundError


class PaymentService:
    def __init__(
            self,
            payment_repository: PaymentsRepository,
            cart_repository: CartRepository,
            order_repository: OrderRepository,
            payment_provider: PaymentProviderInterface
    ):
        self.payment_repository = payment_repository
        self.cart_repository = cart_repository
        self.order_repository = order_repository
        self.payment_provider = payment_provider

    async def initiate_payment(self, order_id: int, user_id: int) -> str:
        try:
            order = await self.order_repository.get_order_by_id(order_id)
        except OrderNotFoundError:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if order.status != OrderStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Order cannot be paid")

        payment_url = await self.payment_provider.initiate_payment(
            order_id=order_id,
            amount=order.total_amount,
            currency="usd"
        )
        
        external_payment_id = self.payment_provider.get_last_payment_intent_id()
        
        existing_payment = await self.payment_repository.get_payment_by_external_id(external_payment_id)
        if existing_payment:
            return payment_url

        payment = Payment(
            user_id=user_id,
            order_id=order_id,
            amount=order.total_amount,
            status=PaymentStatusEnum.PENDING,
            external_payment_id=external_payment_id,
            created_at=datetime.now()
        )

        payment.payment_items = [
            PaymentItem(
                order_item_id=item.id,
                price_at_payment=item.price_at_order
            )
            for item in order.order_items
        ]

        await self.payment_repository.create_payment(payment)
        return payment_url

    async def complete_payment(self, external_payment_id: str) -> Payment:
        payment = await self.payment_repository.get_payment_by_external_id(external_payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status == PaymentStatusEnum.SUCCESSFUL:
            return payment

        if payment.status != PaymentStatusEnum.PENDING and payment.status != PaymentStatusEnum.PROCESSING:
            raise HTTPException(status_code=400, detail="Payment cannot be completed")

        payment_intent = await self.payment_provider.get_payment_intent(external_payment_id)
        
        if payment_intent["status"] == "processing":
            payment.status = PaymentStatusEnum.PROCESSING
            payment = await self.payment_repository.update_payment_status(payment.id, payment.status)
            return payment
        elif payment_intent["status"] == "succeeded":
            payment.status = PaymentStatusEnum.SUCCESSFUL
            await self.order_repository.update_order_status(payment.order_id, OrderStatusEnum.PAID)
            payment = await self.payment_repository.update_payment_status(payment.id, payment.status)
            return payment
        elif payment_intent["status"] == "requires_payment_method" or payment_intent["status"] == "requires_confirmation":
            payment.status = PaymentStatusEnum.PENDING
            payment = await self.payment_repository.update_payment_status(payment.id, payment.status)
            return payment

        payment.status = PaymentStatusEnum.CANCELED
        payment = await self.payment_repository.update_payment_status(payment.id, payment.status)
        return payment

    async def refund_payment(self, order_id: int, user_id: int, amount: Optional[Decimal] = None) -> Payment:
        try:
            order = await self.order_repository.get_order_by_id(order_id)
        except OrderNotFoundError:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        payment = await self.payment_repository.get_successful_payment_by_order_id(order_id)
        if not payment:
            raise HTTPException(status_code=404, detail="No successful payment found for this order")
        if payment.status != PaymentStatusEnum.SUCCESSFUL:
            raise HTTPException(status_code=400, detail="Payment cannot be refunded")

        # Проверяем, не был ли платеж уже возвращен
        if payment.status == PaymentStatusEnum.REFUNDED:
            raise HTTPException(status_code=400, detail="Payment has already been refunded")

        success = await self.payment_provider.refund_payment(payment.external_payment_id, amount)
        if success:
            payment.status = PaymentStatusEnum.REFUNDED
            payment = await self.payment_repository.update_payment_status(payment.id, payment.status)
        else:
            raise HTTPException(status_code=400, detail="Refund failed in payment provider")
        
        return payment

    async def get_user_payments(self, user_id: int) -> Sequence[Payment]:
        payments = await self.payment_repository.get_payments_by_user_id(user_id)
        return payments

    async def get_order_payments(self, order_id: int, user_id: int) -> Sequence[Payment]:
        try:
            order = await self.order_repository.get_order_by_id(order_id)
        except OrderNotFoundError:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        payments = await self.payment_repository.get_payments_by_order_id(order_id)
        return payments
