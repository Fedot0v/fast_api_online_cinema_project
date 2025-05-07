from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.payments import Payment, PaymentStatusEnum, PaymentItem
from src.repositories.base import BaseRepository


class PaymentsRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def update_payment(self, payment: Payment) -> Payment:
        await self.db.merge(payment)
        await self.db.commit()
        return payment

    async def update_payment_status(self, payment_id: int, status: PaymentStatusEnum) -> Payment:
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            raise ValueError("Payment not found")
        payment.status = status
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        return await self.db.get(Payment, payment_id)

    async def get_payment_by_external_id(self, external_payment_id: str) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.external_payment_id == external_payment_id)
        )
        return result.scalars().first()

    async def get_successful_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatusEnum.SUCCESSFUL
            )
        )
        return result.scalars().first()

    async def get_payments_by_user_id(self, user_id: int) -> Sequence[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .options(selectinload(Payment.payment_items))
        )
        return result.scalars().all()

    async def get_payments_by_order_id(self, order_id: int) -> Sequence[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalars().all()
