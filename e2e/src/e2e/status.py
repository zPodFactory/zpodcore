"""Known status string constants.

`ZpodStatus` and `EndpointStatus` are real generated enums in zpodsdk and
are imported directly. Component/zpod-component/download status fields are
plain `str` on the generated SDK models (not enums), so their known values
are mirrored here as constants instead - see zpodcommon/src/zpodcommon/enums.py
in the parent repo for the source of truth if these ever need updating.
"""

from zpodsdk.models.zpod_status import ZpodStatus

ZPOD_TERMINAL_SUCCESS = {ZpodStatus.ACTIVE}
ZPOD_TERMINAL_FAILURE = {ZpodStatus.DEPLOY_FAILED, ZpodStatus.DESTROY_FAILED}
ZPOD_TERMINAL = ZPOD_TERMINAL_SUCCESS | ZPOD_TERMINAL_FAILURE

# zpod-component (component-within-a-zpod) status
ZPOD_COMPONENT_ACTIVE = "ACTIVE"
ZPOD_COMPONENT_ADD_FAILED = "ADD_FAILED"
ZPOD_COMPONENT_DELETE_FAILED = "DELETE_FAILED"
ZPOD_COMPONENT_TERMINAL_FAILURE = {
    ZPOD_COMPONENT_ADD_FAILED,
    ZPOD_COMPONENT_DELETE_FAILED,
}

# library component (global) status
COMPONENT_STATUS_ACTIVE = "ACTIVE"
COMPONENT_STATUS_INACTIVE = "INACTIVE"
# A component its library no longer has (after a resync); listed by `component list --all`.
COMPONENT_STATUS_DELETED = "DELETED"
COMPONENT_STATUSES = {COMPONENT_STATUS_ACTIVE, COMPONENT_STATUS_INACTIVE, COMPONENT_STATUS_DELETED}

# library component download status
DOWNLOAD_STATUS_COMPLETED = "COMPLETED"
DOWNLOAD_STATUS_DOWNLOAD_COMPLETED = "DOWNLOAD_COMPLETED"
DOWNLOAD_STATUS_SUCCESS = {DOWNLOAD_STATUS_COMPLETED, DOWNLOAD_STATUS_DOWNLOAD_COMPLETED}
DOWNLOAD_STATUS_FAILURES = {
    "FAILED_AUTHENTICATION",
    "FAILED_NOT_ENTITLED",
    "FAILED_CHECKSUM",
    "FAILED_UNKNOWN",
    "FAILED_UNSUPPORTED_ENGINE",
}
DOWNLOAD_STATUS_FAILED_AUTHENTICATION = "FAILED_AUTHENTICATION"
DOWNLOAD_STATUS_TERMINAL = DOWNLOAD_STATUS_SUCCESS | DOWNLOAD_STATUS_FAILURES
