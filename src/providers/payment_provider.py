from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional


class PaymentProviderInterface(ABC):
    """Interface for payment provider."""
    @abstractmethod
    async def initiate_payment(
            self,
            order_id: int,
            amount: Decimal,
            currency: str
    ) -> str:
        pass

    @abstractmethod
    async def complete_payment(
            self,
            external_payment_id: str
    ) -> bool:
        pass

    @abstractmethod
    async def refund_payment(
            self,
            external_payment_id: str,
            amount: Optional[Decimal]
    ) -> bool:
        pass