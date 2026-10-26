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
    FAILED_UNSUPPORTED_ENGINE = "FAILED_UNSUPPORTED_ENGINE"
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
    POST_SCRIPTS = "POST_SCRIPTS"
    CONFIG_SCRIPTS = "CONFIG_SCRIPTS"
    ADD_FAILED = "ADD_FAILED"
    DELETE_FAILED = "DELETE_FAILED"


class ZpodNetworkKind(str, Enum):
    # The four networks every zPod deploy creates (management /26 + three routed
    # /26s); created and removed with the zPod only.
    ZPOD = "zpod"
    # Added by a user through POST /zpods/{id}/networks.
    USER = "user"
    # zcore's own VLANs (10, 20, 30 for the nested VCF), configured by the zcore
    # image, listed live from zboxapi (owner system-default); never a row, never
    # changed through zPodFactory.
    ZCORE = "zcore"


class ZpodNetworkRouting(str, Enum):
    # Routed inside the zPod only: zcore is the gateway, nothing on the NSX T1.
    LOCAL = "LOCAL"
    # Advertised to the fabric: a T1 static route sends the subnet to zcore.
    GLOBAL = "GLOBAL"
    # A routing change flow is running; it ends in LOCAL or GLOBAL.
    PENDING = "PENDING"


class ZpodNetworkStatus(str, Enum):
    # Read live from zboxapi on every list, never stored.
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


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
