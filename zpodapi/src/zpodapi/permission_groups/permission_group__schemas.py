from zpodapi.lib.schema_base import Field, SchemaBase
from zpodapi.users.user__schemas import UserView


class D:
    id = {"example": 1}
    name = {"example": "Team"}


class PermissionGroupView(SchemaBase):
    id: int = Field(..., D.id)
    name: str = Field(..., D.name)
    users: list[UserView]


class PermissionGroupCreate(SchemaBase):
    name: str = Field(..., D.name)


class PermissionGroupUpdate(SchemaBase):
    name: str = Field(..., D.name)


class PermissionGroupUserAdd(SchemaBase):
    user_id: int
