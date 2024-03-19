from enum import Enum


class ComponentStatus(str, Enum):
    DELETED = "DELETED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ComponentDownloadStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DOWNLOAD_COMPLETED = "DOWNLOAD_COMPLETED"
    FAILED_AUTHENTICATION = "FAILED_AUTHENTICATION"
    FAILED_NOT_ENTITLED = "FAILED_NOT_ENTITLED"
    FAILED_CHECKSUM = "FAILED_CHECKSUM"
    FAILED_UNKNOWN = "FAILED_UNKNOWN"
    NOT_STARTED = "NOT_STARTED"
    SCHEDULED = "SCHEDULED"
    VERIFYING_CHECKSUM = "VERIFYING_CHECKSUM"


class EndpointPermission(str, Enum):
    USER = "USER"


class InstanceComponentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    ADD_FAILED = "ADD_FAILED"
    DELETE_FAILED = "DELETE_FAILED"


class InstancePermission(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    USER = "USER"


class InstanceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    DELETED = "DELETED"
    DELETING = "DELETING"
    DEPLOY_FAILED = "DEPLOY_FAILED"
    DESTROY_FAILED = "DESTROY_FAILED"
    PENDING = "PENDING"


class UserStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
