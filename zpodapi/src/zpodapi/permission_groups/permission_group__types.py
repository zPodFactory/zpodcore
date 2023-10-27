from zpodapi.lib.id_type_base import IdType


class PermissionGroupIdType(IdType):
    fields = {"id": int, "name": str}
