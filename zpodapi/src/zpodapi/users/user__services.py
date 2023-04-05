from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class UserService(ServiceBase):
    base_model: SQLModel = M.User
