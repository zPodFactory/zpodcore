from enum import Enum


class ZpodStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    CONFIG_SCRIPTS = "CONFIG_SCRIPTS"
    DELETED = "DELETED"
    DELETING = "DELETING"
    DEPLOY_FAILED = "DEPLOY_FAILED"
    DESTROY_FAILED = "DESTROY_FAILED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
