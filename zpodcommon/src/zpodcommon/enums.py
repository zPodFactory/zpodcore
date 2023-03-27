from enum import Enum


class InstanceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    PENDING = "PENDING"
