from zpodapi.lib.id_type_base import IdType


class LibraryIdType(IdType):
    fields = dict(id=int, name=str)
