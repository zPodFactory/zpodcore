from zpodapi.lib.id_type_base import IdType


class EndpointIdType(IdType):
    fields = {"id": int, "name": str}
