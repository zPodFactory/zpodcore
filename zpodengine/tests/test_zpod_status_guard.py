"""No flow writes a status back onto a zPod a destroy owns."""

import pytest

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib.zpod_status import set_zpod_status


@pytest.mark.parametrize("status", ["PENDING", "BUILDING", "DEPLOY_FAILED", "ACTIVE"])
def test_a_live_zpod_takes_the_status(status):
    zpod = M.Zpod(name="lab", endpoint_id=1, status=status, profile="p")
    set_zpod_status(zpod, ZpodStatus.CONFIG_SCRIPTS)
    assert zpod.status == ZpodStatus.CONFIG_SCRIPTS


@pytest.mark.parametrize("status", ["DELETING", "DELETED"])
def test_a_destroyed_zpod_refuses(status):
    zpod = M.Zpod(name="lab", endpoint_id=1, status=status, profile="p")
    with pytest.raises(
        RuntimeError, match=f"lab is {status}: refusing to set it ACTIVE"
    ):
        set_zpod_status(zpod, ZpodStatus.ACTIVE)
    assert zpod.status == status
