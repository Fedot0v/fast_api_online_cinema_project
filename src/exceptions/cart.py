class CartNotFoundError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"Cart not found for user_id {user_id}")

class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"User with id {user_id} not found")

class CartAlreadyExistsError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"Cart already exists for user_id {user_id}")

class MovieNotFoundError(Exception):
    def __init__(self, movie_id: int):
        super().__init__(f"Movie with id {movie_id} not found")

class MovieAlreadyInCartError(Exception):
    def __init__(self, movie_id: int):
        super().__init__(f"Movie with id {movie_id} already in cart")

class MovieNotInCartError(Exception):
    def __init__(self, movie_id: int):
        super().__init__(f"Movie with id {movie_id} not found in cart")