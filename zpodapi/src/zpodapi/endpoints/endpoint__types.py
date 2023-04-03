from zpodapi.lib.id_type_base import IdType


class EndpointIdType(IdType):
    fields = dict(id=int, name=str)
