from enum import Enum


class ZpodNetworkKind(str, Enum):
    USER = "user"
    ZCORE = "zcore"
    ZPOD = "zpod"

    def __str__(self) -> str:
        return str(self.value)
