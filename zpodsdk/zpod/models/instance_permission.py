from enum import Enum


class InstancePermission(str, Enum):
    INSTANCE_ADMIN = "INSTANCE_ADMIN"
    INSTANCE_OWNER = "INSTANCE_OWNER"
    INSTANCE_READ_ONLY = "INSTANCE_READ_ONLY"

    def __str__(self) -> str:
        return str(self.value)
