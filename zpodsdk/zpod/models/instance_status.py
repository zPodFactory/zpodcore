from enum import Enum


class InstanceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    DELETING = "DELETING"
    DELETED = "DELETED"
    PENDING = "PENDING"
    FAILED = "FAILED"

    def __str__(self) -> str:
        return str(self.value)
