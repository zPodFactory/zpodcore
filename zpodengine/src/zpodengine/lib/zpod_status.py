from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus

# A zPod a destroy has taken over: no other flow may write its status again, or it
# would come back to life next to a new zPod of the same name.
GONE = (ZpodStatus.DELETING, ZpodStatus.DELETED)


def set_zpod_status(zpod: M.Zpod, status: ZpodStatus) -> None:
    """Set the status on the row (the caller commits), unless a destroy owns it."""
    if zpod.status in GONE:
        raise RuntimeError(
            f"zPod {zpod.name} is {zpod.status}: refusing to set it {status.value}"
        )
    zpod.status = status
