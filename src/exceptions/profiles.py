class ProfileNotFoundError(Exception):
    """Raised when a user profile is not found."""
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Profile for user {user_id} not found")

class ProfileCreationError(Exception):
    """Raised when profile creation fails."""
    def __init__(self, user_id: int, message: str):
        self.user_id = user_id
        self.message = message
        super().__init__(f"Failed to create profile for user {user_id}: {message}")

class ProfileUpdateError(Exception):
    """Raised when profile update fails."""
    def __init__(self, user_id: int, message: str):
        self.user_id = user_id
        self.message = message
        super().__init__(f"Failed to update profile for user {user_id}: {message}")
