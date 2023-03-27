from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .user__types import UserIdType


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def get(self, *, value: UserIdType):
        id_key, id_value = (value if "=" in value else f"id={value}").split("=")
        return super().get(value=id_value, column=id_key)
