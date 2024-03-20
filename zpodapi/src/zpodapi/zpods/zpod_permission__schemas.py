from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from ..permission_groups.permission_group__schemas import PermissionGroupView
from ..users.user__schemas import UserView


class D:
    id = {"example": 1}
    permission = {"example": enums.ZpodPermission.OWNER}
    user_id = {"example": 1}
    username = {"example": "jdoe"}
    group_id = {"example": 1}
    groupname = {"example": "admins"}


class ZpodPermissionView(SchemaBase):
    id: int = Field(..., D.id)
    permission: enums.ZpodPermission = Field(..., D.permission)
    users: list[UserView] = []
    permission_groups: list[PermissionGroupView] = []


class ZpodPermissionUserAddRemove(SchemaBase):
    user_id: int | None = Field(None, D.user_id)
    username: str | None = Field(None, D.username)


class ZpodPermissionGroupAddRemove(SchemaBase):
    group_id: int | None = Field(None, D.group_id)
    groupname: str | None = Field(None, D.groupname)
