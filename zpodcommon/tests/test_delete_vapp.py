"""delete_vapp waits out VMs that DRS is moving, on fake vApp/VM objects."""

from types import SimpleNamespace

import pytest
from pyVmomi import vim

from zpodcommon.lib import vmware


class FakeVM:
    def __init__(self, name, busy_passes=0):
        self.name = name
        self.busy_passes = busy_passes  # PowerOffVM_Task refused this many times
        self.runtime = SimpleNamespace(powerState="poweredOn")

    def PowerOffVM_Task(self):
        if self.busy_passes:
            self.busy_passes -= 1
            raise vim.fault.TaskInProgress()
        self.runtime.powerState = "poweredOff"


class FakeVApp:
    def __init__(self, vms, destroy_busy=0):
        self.vm = vms
        self.destroy_busy = destroy_busy
        self.destroyed = False

    def Destroy_Task(self):
        assert all(vm.runtime.powerState == "poweredOff" for vm in self.vm)
        if self.destroy_busy:
            self.destroy_busy -= 1
            raise vim.fault.VAppTaskInProgress()
        self.destroyed = True


@pytest.fixture
def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(vmware.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(vmware.time, "sleep", lambda s: now.__setitem__(0, now[0] + s))
    monkeypatch.setattr(vmware.task, "WaitForTask", lambda t: None)
    return now


def make_vc(vapp):
    vc = object.__new__(vmware.vCenter)
    vc.get_vapp = lambda name: None if vapp.destroyed else vapp
    return vc


def test_waits_for_vmotions_then_destroys(clock):
    moving = FakeVM("esxi12", busy_passes=3)
    vapp = FakeVApp(
        [FakeVM("zcore"), moving, FakeVM("esxi13", busy_passes=1)], destroy_busy=1
    )
    make_vc(vapp).delete_vapp("zpod-x", poll=10)
    assert vapp.destroyed
    assert clock[0] == 40  # 3 passes waiting on esxi12, 1 on the vApp destroy


def test_gives_up_after_timeout(clock):
    vapp = FakeVApp([FakeVM("esxi11", busy_passes=1000)])
    with pytest.raises(TimeoutError, match="esxi11"):
        make_vc(vapp).delete_vapp("zpod-x", timeout=60, poll=10)
    assert not vapp.destroyed


def test_absent_vapp_is_a_noop(clock):
    vc = object.__new__(vmware.vCenter)
    vc.get_vapp = lambda name: None
    vc.delete_vapp("zpod-x")
