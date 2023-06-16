from zpodapi.lib.id_type_base import IdType


class ProfileIdType(IdType):
    fields = dict(id=int, name=str)
