from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .user__types import UserIdType


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def get(self, *, id: UserIdType):
        id_key, id_value = (id if "=" in id else f"id={id}").split("=")
        return super().get(**{id_key: id_value})
