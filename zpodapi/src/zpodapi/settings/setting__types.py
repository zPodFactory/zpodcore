from zpodapi.lib.id_type_base import IdType


class SettingIdType(IdType):
    fields = dict(id=int, name=str)
