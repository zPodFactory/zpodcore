from enum import Enum


class ZpodNetworkRouting(str, Enum):
    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
