from enum import Enum


class InstanceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETING = "DELETING"
    DELETED = "DELETED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
