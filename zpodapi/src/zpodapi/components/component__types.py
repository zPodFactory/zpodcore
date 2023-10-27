from zpodapi.lib.id_type_base import IdType


class ComponentIdType(IdType):
    fields = {"id": int, "uid": str}
    arg_mapper = {"uid": "component_uid"}
