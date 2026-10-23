from enum import Enum


class ZpodDiskStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MISSING = "MISSING"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return str(self.value)
