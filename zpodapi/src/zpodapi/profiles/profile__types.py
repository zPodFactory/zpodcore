from zpodapi.lib.id_type_base import IdType


class ProfileIdType(IdType):
    fields = {"id": int, "name": str}
