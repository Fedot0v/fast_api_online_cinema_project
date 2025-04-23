from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MovieBaseSchema(BaseModel):
    id: int
    uuid: UUID
    title: str
    year: int
    time: int
    imdb: float
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: float
    certification_id: int

    model_config = {
        "from_attributes": True
    }


class CommentCreateSchema(BaseModel):
     content: str = Field(..., min_length=1, max_length=1000)
     parent_comment_id: Optional[int] = None


class CommentReplySchema(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CommentResponseSchema(BaseModel):
    id: int
    movie_id: int
    user_id: int
    content: str
    created_at: datetime
    replies: list[CommentReplySchema] = []

    model_config = {
        "from_attributes": True
    }


class FavoriteCreateSchema(BaseModel):
    movie_id: int


class FavoriteResponseSchema(BaseModel):
    user_id: int
    movie_id: int
    movie: MovieBaseSchema

    model_config = {
        "from_attributes": True
    }
