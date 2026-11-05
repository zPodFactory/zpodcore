"""vCenter retries after a dropped connection, on a fake pyVmomi stub.

vCenter sometimes closes every open connection at once under load: replay the
calls that are safe to repeat, never a task such as PowerOnVM_Task.
"""

import http.client
from types import SimpleNamespace

import pytest
from pyVmomi import vim, vmodl

from zpodcommon.lib import vmware


class FakeStub:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def InvokeMethod(self, mo, info, args, outerStub=None):
        self.calls.append(info.wsdlName)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(vmware.time, "sleep", lambda _: None)


def make_vc(*outcomes, logins=None):
    vc = object.__new__(vmware.vCenter)
    vc.host, vc.user, vc.pwd = "vcsa.example.com", "user", "pwd"
    session_manager = SimpleNamespace(Login=lambda u, p: logins.append((u, p)))
    vc.si = SimpleNamespace(
        _stub=FakeStub(outcomes),
        RetrieveContent=lambda: SimpleNamespace(sessionManager=session_manager),
    )
    vc._install_retrying_stub()
    return vc


def call(vc, method):
    return vc.si._stub.InvokeMethod(None, SimpleNamespace(wsdlName=method), ())


def dropped():
    return http.client.RemoteDisconnected("Remote end closed connection")


def test_read_is_replayed_after_dropped_connection():
    vc = make_vc(dropped(), ConnectionResetError(), "info")
    assert call(vc, "Fetch") == "info"
    assert vc.si._stub.calls == ["Fetch"] * 3


def test_read_gives_up_after_all_retries():
    vc = make_vc(*[dropped()] * (vmware.VCENTER_RETRIES + 1))
    with pytest.raises(http.client.RemoteDisconnected):
        call(vc, "RetrievePropertiesEx")
    assert len(vc.si._stub.calls) == vmware.VCENTER_RETRIES + 1


def test_task_is_not_replayed_after_dropped_connection():
    vc = make_vc(dropped(), "task")
    with pytest.raises(http.client.RemoteDisconnected):
        call(vc, "PowerOnVM_Task")
    assert vc.si._stub.calls == ["PowerOnVM_Task"]


def test_task_is_replayed_when_connection_was_refused():
    vc = make_vc(ConnectionRefusedError(), "task")
    assert call(vc, "PowerOnVM_Task") == "task"


def test_api_fault_is_not_replayed():
    vc = make_vc(vim.fault.InvalidPowerState(), "info")
    with pytest.raises(vim.fault.InvalidPowerState):
        call(vc, "Fetch")
    assert vc.si._stub.calls == ["Fetch"]


def test_lost_session_logs_in_again_once():
    logins = []
    vc = make_vc(vim.fault.NotAuthenticated(), "info", logins=logins)
    assert call(vc, "Fetch") == "info"
    assert logins == [("user", "pwd")]

    vc = make_vc(*[vim.fault.NotAuthenticated()] * 2, logins=logins)
    with pytest.raises(vim.fault.NotAuthenticated):
        call(vc, "Fetch")


def test_replayed_destroy_filter_already_gone_is_ok():
    vc = make_vc(dropped(), vmodl.fault.ManagedObjectNotFound())
    assert call(vc, "DestroyFilter") is None

    vc = make_vc(vmodl.fault.ManagedObjectNotFound())
    with pytest.raises(vmodl.fault.ManagedObjectNotFound):
        call(vc, "DestroyFilter")


def test_connect_retries_then_raises_connection_error(monkeypatch):
    attempts = []

    def smart_connect(**_):
        attempts.append(1)
        raise ConnectionResetError()

    monkeypatch.setattr(vmware.connect, "SmartConnect", smart_connect)
    with pytest.raises(ConnectionError, match="Unable to connect to host"):
        vmware.vCenter(host="vcsa.example.com", user="user", pwd="pwd")
    assert len(attempts) == vmware.VCENTER_RETRIES + 1
