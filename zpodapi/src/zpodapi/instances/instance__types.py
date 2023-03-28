from zpodapi.lib.id_type_base import IdType


class InstanceIdType(IdType):
    fields = dict(id=int, name=str)
