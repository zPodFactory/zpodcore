class IdType(str):
    fields = dict(id=int)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        v = v.lower()
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
    def parse(value) -> tuple[str, str]:
        return (value if "=" in value else f"id={value}").split("=")

    def __repr__(self):
        return f"{self.__class__.__name__}()"
