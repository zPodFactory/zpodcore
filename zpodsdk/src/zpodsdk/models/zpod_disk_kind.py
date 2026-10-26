from enum import Enum


class ZpodDiskKind(str, Enum):
    USER = "user"
    ZPOD = "zpod"

    def __str__(self) -> str:
        return str(self.value)
