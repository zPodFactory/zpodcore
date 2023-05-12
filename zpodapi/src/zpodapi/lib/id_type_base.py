from typing import Any


class IdType(str):
    fields = dict(id=int)
    arg_mapper = {}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str):
        if not isinstance(v, str):
            raise TypeError("string required")
        column, value = cls.parse(v)
        if column not in cls.fields:
            raise ValueError(f"Invalid Key: {column}")

        fldtype = cls.fields[column]
        if getattr(fldtype, "validate", None):
            fldtype.validate(value)
        elif fldtype == int:
            try:
                int(value)
            except ValueError as e:
                raise ValueError(f"value is not a valid integer: {value}") from e
        return cls(v)

    @staticmethod
    def parse(text: str) -> tuple[str, str]:
        return (text if "=" in text else f"id={text}").split("=")

    @classmethod
    def args(cls, text: str) -> dict[str, Any]:
        col, val = cls.parse(text)
        if col in cls.arg_mapper:
            col = cls.arg_mapper[col]
        if col != "id":
            col = f"{col}_insensitive"
        return {col: val}

    def __repr__(self):
        return f"{self.__class__.__name__}()"
