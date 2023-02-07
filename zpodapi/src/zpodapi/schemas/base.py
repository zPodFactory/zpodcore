from functools import wraps

from sqlmodel import Field


def field(func: Field) -> Field:
    """Allow argument example="Example", instead of using
    schema_extra=dict(example="Example")."""

    @wraps(func)
    def inner(*args, example=None, **kwargs):
        if example:
            kwargs.setdefault("schema_extra", {})
            kwargs["schema_extra"]["example"] = example
        return func(*args, **kwargs)

    return inner


Field = field(Field)
