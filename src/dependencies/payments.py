from fastapi import Depends
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.dependencies.movies import get_repository
from src.providers.stripe_payment_provider import StripePaymentProvider
from src.repositories.cart.cart_rep import CartRepository
from src.repositories.orders.order_repo import OrderRepository
from src.repositories.payments.payments_repo import PaymentsRepository
from src.services.payments.payments_service import PaymentService


async def get_settings_dependency() -> BaseSettings:
    return get_settings()


async def get_payment_provider(settings: BaseSettings = Depends(get_settings_dependency)) -> StripePaymentProvider:
    return StripePaymentProvider(api_key=settings.STRIPE_API_KEY)


async def get_payment_service(
    provider: StripePaymentProvider = Depends(get_payment_provider),
    order_repository: OrderRepository = Depends(get_repository(OrderRepository)),
    payment_repository: PaymentsRepository = Depends(get_repository(PaymentsRepository)),
    cart_repository: CartRepository = Depends(get_repository(CartRepository)),
) -> PaymentService:
    return PaymentService(
        payment_provider=provider,
        order_repository=order_repository,
        payment_repository=payment_repository,
        cart_repository=cart_repository,
    )
