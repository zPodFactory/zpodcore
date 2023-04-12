from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from ..permission_groups.permission_group__schemas import PermissionGroupView
from ..users.user__schemas import UserView


class D:
    id = {"example": 1}
    permission = {"example": enums.InstancePermission.INSTANCE_OWNER}


class InstancePermissionView(SchemaBase):
    id: int = Field(..., D.id)
    permission: enums.InstancePermission = Field(..., D.permission)
    users: list[UserView] = []
    groups: list[PermissionGroupView] = []
