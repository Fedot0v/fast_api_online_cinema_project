from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic.v1 import BaseModel


class OrderItemResponse(BaseModel):
    movie_id: int
    price_at_order: Decimal


class OrderCreateResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: str
    total_amount: Decimal
    order_items: List[dict[str, OrderItemResponse]]
    excluded_movie_ids: List[int]