from sqlalchemy import event

from typing import Type, TypeVar


T = TypeVar("T")


def normalize_name(name: str) -> str:
    """
    Normalize a name by converting to lowercase and removing spaces.

    Args:
        name: The input name to normalize.

    Returns:
        Normalized name as a string.

    Raises:
        ValueError: If the input name is empty or None.
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty or None")
    return "".join(name.lower().split())


def with_normalized_name_events(model_class: Type[T]) -> Type[T]:
    """
    Class decorator to apply before_insert and before_update events for setting normalized_name.

    Args:
        model_class: SQLAlchemy model class with name and normalized_name fields.

    Returns:
        The same model class with event listeners attached.
    """

    def set_normalized_name(mapper, connection, target):
        target.normalized_name = normalize_name(target.name)

    event.listen(model_class, "before_insert", set_normalized_name)
    event.listen(model_class, "before_update", set_normalized_name)
    return model_class