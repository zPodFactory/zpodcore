from enum import Enum


class InstanceStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
