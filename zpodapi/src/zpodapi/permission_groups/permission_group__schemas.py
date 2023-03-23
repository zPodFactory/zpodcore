from datetime import datetime

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Req
from zpodapi.users.user__schemas import UserView

example_creation_date = datetime(2023, 1, 1)


class PermissionGroupView(SQLModel):
    id: int = Req(example=1)
    name: str = Req(example="Team")
    users: list[UserView]
