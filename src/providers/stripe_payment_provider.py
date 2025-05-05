import asyncio
from decimal import Decimal
from typing import Optional

import stripe

from src.providers.payment_provider import PaymentProviderInterface


class StripePaymentProvider(PaymentProviderInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = stripe
        self.client.api_key = api_key

    async def initiate_payment(self, order_id: str, amount: Decimal, currency: str) -> str:
        try:
            payment_params = {
                "amount": int(amount * 100),
                "currency": currency.lower(),
                "metadata": {"order_id": order_id},
                "description": f"Payment for order #{order_id}"
            }
            payment_intent = await asyncio.to_thread(
                self.client.PaymentIntent.create,
                **payment_params
            )
            return payment_intent["client_secret"]
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")

    async def complete_payment(self, external_payment_id: str) -> bool:
        try:
            payment_intent = await asyncio.to_thread(
                self.client.PaymentIntent.retrieve,
                external_payment_id
            )
            return payment_intent["status"] == "succeeded"
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")

    async def refund_payment(self, external_payment_id: str, amount: Optional[Decimal] = None) -> bool:
        try:
            refund_params = {
                "payment_intent": external_payment_id,
            }
            if amount is not None:
                refund_params["amount"] = int(amount * 100)
            refund = await asyncio.to_thread(
                self.client.Refund.create,
                **refund_params
            )
            return refund["status"] == "succeeded"
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")
