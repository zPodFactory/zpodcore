from zpodapi.lib.id_type_base import IdType


class InstanceComponentIdType(IdType):
    fields = {"id": int, "hostname": str}
