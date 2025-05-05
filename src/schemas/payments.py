from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel



class PaymentItemResponse(BaseModel):
    order_item_id: int
    price_at_payment: Decimal

    model_config = {
        "from_attributes": True
    }

class PaymentDetailResponse(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: str
    amount: Decimal
    external_payment_id: Optional[str]
    payment_items: List[PaymentItemResponse]

    model_config = {
        "from_attributes": True
    }


class PaymentResponse(BaseModel):
    client_secret: str


class RefundRequest(BaseModel):
    amount: Optional[float] = None
