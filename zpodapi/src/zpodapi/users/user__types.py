from pydantic import EmailStr

from zpodapi.lib.id_type_base import IdType


class UserIdType(IdType):
    fields = dict(id=int, username=str, email=EmailStr)
