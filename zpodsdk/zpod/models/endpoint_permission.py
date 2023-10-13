from enum import Enum


class EndpointPermission(str, Enum):
    USER = "USER"

    def __str__(self) -> str:
        return str(self.value)
