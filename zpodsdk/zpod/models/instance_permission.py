from enum import Enum


class InstancePermission(str, Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    USER = "USER"

    def __str__(self) -> str:
        return str(self.value)
