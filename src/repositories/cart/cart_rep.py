import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import UserModel
from src.database.models.cart import CartModel, CartItemsModel
from src.database.models.movies import MovieModel
from src.exceptions.cart import (
    MovieNotInCartError,
    MovieAlreadyInCartError,
    MovieNotFoundError,
    CartAlreadyExistsError,
    UserNotFoundError,
    CartNotFoundError
)
from src.repositories.base import BaseRepository


logger = logging.getLogger(__name__)


class CartRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def exists(self, user_id: int) -> bool:
        """Check if cart exists for user."""
        stmt = select(CartModel).where(CartModel.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_by_user_id(self, user_id: int) -> CartModel:
        """Get cart with items and movies loaded."""
        stmt = (
            select(CartModel)
            .where(CartModel.user_id == user_id)
            .options(
                selectinload(CartModel.cart_items)
                .selectinload(CartItemsModel.movie)
            )
        )
        result = await self.db.execute(stmt)
        cart = result.scalars().first()
        if not cart:
            raise CartNotFoundError(user_id)
        return cart

    async def _create(self, user_id: int) -> CartModel:
        """Create a new cart for the user. Protected method for internal use."""
        user = await self.db.get(UserModel, user_id)
        if not user:
            raise UserNotFoundError(user_id)
        if await self.exists(user_id):
            raise CartAlreadyExistsError(user_id)
        cart = CartModel(user_id=user_id)
        self.db.add(cart)
        await self.db.commit()
        await self.db.refresh(cart)
        return cart

    async def delete(self, user_id: int) -> None:
        """Delete the user's cart."""
        cart = await self.get_by_user_id(user_id)
        await self.db.delete(cart)
        await self.db.commit()

    async def item_exists(self, cart_id: int, movie_id: int) -> bool:
        """Check if movie exists in the cart."""
        stmt = select(CartItemsModel).where(
            CartItemsModel.cart_id == cart_id,
            CartItemsModel.movie_id == movie_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_movie(self, user_id: int, movie_id: int) -> CartItemsModel:
        """Add a movie to the user's cart. Create cart if it doesn't exist."""
        try:
            movie = await self.db.get(MovieModel, movie_id)
            if not movie:
                raise MovieNotFoundError(movie_id)

            cart = await (
                self.get_by_user_id(user_id)
            ) if await self.exists(user_id) else await self._create(user_id)

            if await self.item_exists(cart.id, movie_id):
                raise MovieAlreadyInCartError(movie_id)

            cart_item = CartItemsModel(cart_id=cart.id, movie_id=movie_id)
            self.db.add(cart_item)
            await self.db.flush()

            stmt = (
                select(CartItemsModel)
                .where(CartItemsModel.id == cart_item.id)
                .options(selectinload(CartItemsModel.movie))
            )
            result = await self.db.execute(stmt)
            cart_item = result.scalars().first()

            await self.db.commit()
            return cart_item

        except (MovieNotFoundError, CartNotFoundError, MovieAlreadyInCartError):
            await self.db.rollback()
            raise

        except Exception as e:
            logger.error(f"Error adding movie to cart: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise

    async def remove_movie(self, user_id: int, movie_id: int) -> CartItemsModel:
        """Remove a movie from the user's cart. Return removed item."""
        try:
            cart = await self.get_by_user_id(user_id)
            stmt = select(CartItemsModel).where(
                CartItemsModel.cart_id == cart.id,
                CartItemsModel.movie_id == movie_id
            ).options(selectinload(CartItemsModel.movie))
            result = await self.db.execute(stmt)
            cart_item = result.scalar_one_or_none()
            if not cart_item:
                raise MovieNotInCartError(movie_id)
            await self.db.delete(cart_item)
            await self.db.commit()
            return cart_item

        except (CartNotFoundError, MovieNotInCartError):
            await self.db.rollback()
            raise

        except Exception as e:
            logger.error(f"Error removing movie from cart: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
