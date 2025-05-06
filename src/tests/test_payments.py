import pytest
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from src.database.models.orders import OrderStatusEnum, Orders
from src.database.models.payments import PaymentStatusEnum, Payment


@pytest.mark.asyncio
async def test_initiate_payment_success(
    payment_service,
    order_repository,
    test_user,
):
    order_id = 1
    user_id = test_user.id
    total_amount = Decimal("100.00")
    
    order = Orders(
        user_id=user_id,
        total_amount=total_amount,
        status=OrderStatusEnum.PENDING,
        created_at=datetime.now()
    )
    order = await order_repository.create_order(order)
    
    payment_url = await payment_service.initiate_payment(order.id, user_id)
    
    assert payment_url.startswith("https://payment.test/")
    assert payment_url.endswith(str(order.id))


@pytest.mark.asyncio
async def test_initiate_payment_order_not_found(payment_service, test_user):
    non_existent_order_id = 9999
    user_id = test_user.id
    
    with pytest.raises(HTTPException) as exc_info:
        await payment_service.initiate_payment(non_existent_order_id, user_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Order not found"


@pytest.mark.asyncio
async def test_initiate_payment_unauthorized(
    payment_service,
    order_repository,
    test_user
):
    wrong_user_id = test_user.id + 1
    order = Orders(
        user_id=test_user.id,
        total_amount=Decimal("100.00"),
        status=OrderStatusEnum.PENDING,
        created_at=datetime.now()
    )
    order = await order_repository.create_order(order)
    
    with pytest.raises(HTTPException) as exc_info:
        await payment_service.initiate_payment(order.id, wrong_user_id)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorized"


@pytest.mark.asyncio
async def test_complete_payment_success(
    payment_service,
    payment_repository,
    order_repository,
    test_user
):
    order = Orders(
        user_id=test_user.id,
        total_amount=Decimal("100.00"),
        status=OrderStatusEnum.PENDING,
        created_at=datetime.now()
    )
    order = await order_repository.create_order(order)
    
    payment = Payment(
        user_id=test_user.id,
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatusEnum.PENDING,
        external_payment_id=f"pi_{order.id}",
        created_at=datetime.now()
    )
    await payment_repository.create_payment(payment)
    
    completed_payment = await payment_service.complete_payment(f"pi_{order.id}")
    
    assert completed_payment.status == PaymentStatusEnum.SUCCESSFUL
    updated_order = await order_repository.get_order_by_id(order.id)
    assert updated_order.status == OrderStatusEnum.PAID


@pytest.mark.asyncio
async def test_refund_payment_success(
    payment_service,
    payment_repository,
    order_repository,
    test_user
):
    order = Orders(
        user_id=test_user.id,
        total_amount=Decimal("100.00"),
        status=OrderStatusEnum.PAID,
        created_at=datetime.now()
    )
    order = await order_repository.create_order(order)
    
    payment = Payment(
        user_id=test_user.id,
        order_id=order.id,
        amount=Decimal("100.00"),
        status=PaymentStatusEnum.SUCCESSFUL,
        external_payment_id=f"pi_{order.id}",
        created_at=datetime.now()
    )
    payment = await payment_repository.create_payment(payment)
    
    refunded_payment = await payment_service.refund_payment(
        order_id=order.id,
        user_id=test_user.id,
        amount=Decimal("100.00")
    )

    assert refunded_payment.status == PaymentStatusEnum.REFUNDED


@pytest.mark.asyncio
async def test_get_user_payments(
    payment_service,
    payment_repository,
    test_user
):
    payment1 = Payment(
        user_id=test_user.id,
        order_id=1,
        amount=Decimal("100.00"),
        status=PaymentStatusEnum.SUCCESSFUL,
        created_at=datetime.now()
    )
    payment2 = Payment(
        user_id=test_user.id,
        order_id=2,
        amount=Decimal("200.00"),
        status=PaymentStatusEnum.SUCCESSFUL,
        created_at=datetime.now()
    )
    await payment_repository.create_payment(payment1)
    await payment_repository.create_payment(payment2)
    
    payments = await payment_service.get_user_payments(test_user.id)
    
    assert len(payments) == 2
    assert all(p.user_id == test_user.id for p in payments)


@pytest.mark.asyncio
async def test_get_order_payments(
    payment_service,
    payment_repository,
    order_repository,
    test_user
):
    order = Orders(
        user_id=test_user.id,
        total_amount=Decimal("100.00"),
        status=OrderStatusEnum.PENDING,
        created_at=datetime.now()
    )
    order = await order_repository.create_order(order)
    
    payment1 = Payment(
        user_id=test_user.id,
        order_id=order.id,
        amount=Decimal("50.00"),
        status=PaymentStatusEnum.SUCCESSFUL,
        created_at=datetime.now()
    )
    payment2 = Payment(
        user_id=test_user.id,
        order_id=order.id,
        amount=Decimal("50.00"),
        status=PaymentStatusEnum.SUCCESSFUL,
        created_at=datetime.now()
    )
    await payment_repository.create_payment(payment1)
    await payment_repository.create_payment(payment2)
    
    payments = await payment_service.get_order_payments(order.id, test_user.id)
    
    assert len(payments) == 2
    assert all(p.order_id == order.id for p in payments)
    assert all(p.user_id == test_user.id for p in payments) 
