from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import UserModel
from src.database.models.movies import MovieCommentModel
from src.repositories.base import BaseRepository


class CommentsRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_comment(
            self,
            user_id: int,
            movie_id: int,
            content: str,
            parent_comment_id: Optional[int] = None
    ) -> MovieCommentModel:
        comment = MovieCommentModel(
            user_id=user_id,
            movie_id=movie_id,
            content=content,
            parent_comment_id=parent_comment_id
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_comment_by_id(
            self,
            comment_id: int
    ) -> Optional[MovieCommentModel]:
        stmt = (
            select(MovieCommentModel)
            .where(MovieCommentModel.id == comment_id)
            .options(
                joinedload(MovieCommentModel.user)
                .joinedload(UserModel.profile)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_movie_comments(
            self,
            movie_id: int
    ) -> Sequence[MovieCommentModel]:
        stmt = (
            select(MovieCommentModel)
            .where(
                MovieCommentModel.movie_id == movie_id,
                MovieCommentModel.parent_comment_id.is_(None)
            )
            .options(
                joinedload(MovieCommentModel.user),
                joinedload(MovieCommentModel.parent)
                .joinedload(MovieCommentModel.user),
                joinedload(MovieCommentModel.likes)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_comment(self, comment_id: int) -> None:
        stmt = delete(MovieCommentModel).where(
            MovieCommentModel.id == comment_id
        )
        await self.db.execute(stmt)
        await self.db.commit()
