from enum import Enum


class InstanceStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    PENDING = "PENDING"
