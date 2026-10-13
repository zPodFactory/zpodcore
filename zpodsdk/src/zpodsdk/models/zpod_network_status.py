from enum import Enum


class ZpodNetworkStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return str(self.value)
