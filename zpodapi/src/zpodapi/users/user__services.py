from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .user__types import UserIdType


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def get(self, *, value: UserIdType):
        column, value = UserIdType.parse(value)
        return super().get(value=value, column=column)
