from enum import Enum


class ComponentStatus(str, Enum):
    FAILED_DOWNLOAD = "FAILED_DOWNLOAD"
    NOT_ENTITLED = "NOT_ENTITLED"
    DOWNLOAD_COMPLETE = "DOWNLOAD_COMPLETE"
    FAILED_AUTHENTICATION = "FAILED_AUTHENTICATION"
    SCHEDULED = "SCHEDULED"
    DOWNLOAD_INCOMPLETE = "DOWNLOAD_INCOMPLETE"


class InstancePermission(str, Enum):
    INSTANCE_ADMIN = "INSTANCE_ADMIN"
    INSTANCE_OWNER = "INSTANCE_OWNER"
    INSTANCE_READ_ONLY = "INSTANCE_READ_ONLY"


class InstanceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    PENDING = "PENDING"
