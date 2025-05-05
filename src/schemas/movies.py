from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field
from pydantic.v1 import validator


class MovieBase(BaseModel):
    id: int
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


class MovieCreateSchema(BaseModel):
    title: str
    year: int
    time: int
    imdb: float
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: float
    certification_id: int
    genre_ids: List[int] = []
    star_ids: List[int] = []
    director_ids: List[int] = []

    @validator("imdb")
    def validate_imdb(cls, v):
        if not 0 <= v <= 10:
            raise ValueError("IMDB rating must be between 0 and 10")
        return v


class MovieDetail(MovieBase):
    average_rating: float = 0.0
    genres: List[str] = []
    directors: List[str] = []
    stars: List[str] = []

    model_config = {
        "from_attributes": True
    }


class StarBaseSchema(BaseModel):
    name: str


class StarResponseSchema(StarBaseSchema):
    id: int


class GenreBaseSchema(BaseModel):
    name: str


class GenreResponseSchema(GenreBaseSchema):
    id: int


class MovieQuery(BaseModel):
    skip: int = 0
    limit: int = 10
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    filters: Optional[Dict[str, str]] = None
    search_criteria: Optional[Dict[str, str]] = None
    partial_match: bool = True


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
    replies: Optional[list[CommentReplySchema]] = []

    model_config = {
        "from_attributes": True
    }


class FavoriteCreateSchema(BaseModel):
    movie_id: int


class FavoriteResponseSchema(BaseModel):
    user_id: int
    movie_id: int
    movie: MovieBase

    model_config = {
        "from_attributes": True
    }


class DirectorBaseSchema(BaseModel):
    name: str


class DirectorResponseSchema(DirectorBaseSchema):
    id: int


class RatingCreate(BaseModel):
    rating: int

    @validator("rating")
    def validate_rating(cls, value):
        if not 1 <= value <= 10:
            raise ValueError("Rating must be between 1 and 10")
        return value


class RatingResponse(BaseModel):
    rating: int
    movie_id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }


class RatingAverageResponse(BaseModel):
    movie_id: int
    average_rating: float


class CertificationCreateSchema(BaseModel):
    name: str


class CertificationOutSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }
