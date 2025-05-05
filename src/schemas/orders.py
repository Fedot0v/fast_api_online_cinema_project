from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    movie_id: int
    price_at_order: Decimal

    model_config = {
        "from_attributes": True
    }

class OrderCreateResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: str
    total_amount: Decimal
    order_items: List[OrderItemResponse]
    excluded_movie_ids: List[int]

    model_config = {
        "from_attributes": True
    }