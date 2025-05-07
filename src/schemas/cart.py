from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, PositiveInt


class BaseCartModel(BaseModel):
    id: PositiveInt


class MovieInCartResponse(BaseCartModel):
    title: str
    year: Optional[int] = None
    price: Decimal

    model_config = {
        "from_attributes": True
    }

class CartItemResponse(BaseCartModel):
    cart_id: PositiveInt
    movie_id: PositiveInt
    added_at: datetime
    movie: Optional[MovieInCartResponse] = None

    model_config = {
        "from_attributes": True
    }

class CartResponse(BaseCartModel):
    user_id: PositiveInt
    total_amount: Decimal
    cart_items: List[CartItemResponse] = []

    model_config = {
        "from_attributes": True
    }

class MovieToCartRequest(BaseModel):
    movie_id: PositiveInt