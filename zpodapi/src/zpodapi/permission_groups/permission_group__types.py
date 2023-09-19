from zpodapi.lib.id_type_base import IdType


class PermissionGroupIdType(IdType):
    fields = dict(id=int, name=str)
