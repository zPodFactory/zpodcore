from enum import Enum


class CaseInsensitiveEnum(Enum):
    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        return next(
            (member for member in cls if member.lower() == value),
            None,
        )


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


class EndpointComputeDrivers(str, CaseInsensitiveEnum):
    VSPHERE = "vsphere"


class EndpointNetworkDrivers(str, CaseInsensitiveEnum):
    NSXT = "nsxt"
    NSXT_PROJECTS = "nsxt_projects"


class EndpointPermission(str, Enum):
    USER = "USER"


class EndpointStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class UserStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class ZpodComponentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    CONFIG_SCRIPTS = "CONFIG_SCRIPTS"
    ADD_FAILED = "ADD_FAILED"
    DELETE_FAILED = "DELETE_FAILED"


class ZpodPermission(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    USER = "USER"


class ZpodStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BUILDING = "BUILDING"
    CONFIG_SCRIPTS = "CONFIG_SCRIPTS"
    DELETED = "DELETED"
    DELETING = "DELETING"
    DEPLOY_FAILED = "DEPLOY_FAILED"
    DESTROY_FAILED = "DESTROY_FAILED"
    PENDING = "PENDING"
