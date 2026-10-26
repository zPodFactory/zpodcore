from enum import Enum


class ZpodStorageKind(str, Enum):
    USER = "user"
    ZCORE = "zcore"

    def __str__(self) -> str:
        return str(self.value)
