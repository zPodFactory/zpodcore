from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from ..permission_groups.permission_group__schemas import PermissionGroupView
from ..users.user__schemas import UserView


class D:
    id = {"example": 1}
    permission = {"example": enums.EndpointPermission.USER}
    user_id = {"example": 1}
    username = {"example": "jdoe"}
    group_id = {"example": 1}
    groupname = {"example": "admins"}


class EndpointPermissionView(SchemaBase):
    id: int = Field(..., D.id)
    permission: enums.EndpointPermission = Field(..., D.permission)
    users: list[UserView] = []
    permission_groups: list[PermissionGroupView] = []


class EndpointPermissionUserAddRemove(SchemaBase):
    user_id: int | None = Field(None, D.user_id)
    username: str | None = Field(None, D.username)


class EndpointPermissionGroupAddRemove(SchemaBase):
    group_id: int | None = Field(None, D.group_id)
    groupname: str | None = Field(None, D.groupname)
