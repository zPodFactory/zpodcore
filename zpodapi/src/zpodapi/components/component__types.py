from zpodapi.lib.id_type_base import IdType


class ComponentIdType(IdType):
    fields = dict(id=int, uid=str)
