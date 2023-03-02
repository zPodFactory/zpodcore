from pydantic import EmailStr


class UserIdType(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        v = v.lower()
        idtype, id_ = (v if "=" in v else f"id={v}").split("=")
        if idtype not in ("id", "username", "email"):
            raise ValueError(f"Invalid ID Type: {idtype}")
        if idtype == "id":
            int(id_)
        elif idtype == "email":
            EmailStr.validate(id_)
        return cls(v)

    def __repr__(self):
        return f"UserId({super().__repr__()})"
