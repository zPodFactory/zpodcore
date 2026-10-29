"""ovf_deployer with and without component_deploy_extra_config, on both deploy paths.

govc, vCenter and the OVA staging are faked; what is checked is the order: the VM
is created powered off, then its guestinfo.* keys are set, on the direct import and
on the staging clone alike. A component without the key deploys as before.
"""

import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from zpodengine.lib import ova_staging, ovfdeployer
from zpodengine.lib.deploy_spec import ExtraConfigError

GOVC_SPEC = {
    "DiskProvisioning": "thin",
    "NetworkMapping": [{"Name": "VM Network", "Network": "{{zpod_portgroup}}"}],
    "PowerOn": True,
    "InjectOvfEnv": False,
}
EXTRA = {
    "guestinfo.metadata": {
        "format": "yaml",
        "content": {
            "instance-id": "{{zpod_hostname}}",
            "local-hostname": "{{zpod_hostname}}",
        },
    }
}


class World:
    """Records what the deployer does, in order."""

    def __init__(self):
        self.events: list[tuple] = []
        self.staging = None  # None: ff_endpoint_ova_staging off; "ok" | "fail"
        self.vm_exists = False


@pytest.fixture
def world(tmp_path, monkeypatch):
    w = World()

    settings = {
        "zpodfactory_host": "10.42.111.1",
        "zpodfactory_ssh_key": "ssh-ed25519 K",
    }
    monkeypatch.setattr(
        ovfdeployer.DBUtils,
        "get_setting_value",
        classmethod(
            lambda cls, name: (
                ("true" if w.staging else None)
                if name == "ff_endpoint_ova_staging"
                else settings.get(name)
            )
        ),
    )
    monkeypatch.setattr(
        ovfdeployer.MgmtIp,
        "zpod",
        classmethod(
            lambda cls, zpod, name: SimpleNamespace(
                ip="10.42.111.1" if name == "gw" else "10.42.111.2",
                netmask="255.255.255.0",
            )
        ),
    )

    def cmd_execute(cmd):
        options_file = cmd.split("-options=")[1].split()[0]
        with open(options_file) as f:
            options = json.load(f)
        w.events.append(("import", options["PowerOn"]))
        w.vm_exists = True

    monkeypatch.setattr(ovfdeployer, "cmd_execute", cmd_execute)

    def deploy_from_template(**kw):
        if w.staging == "fail":
            raise RuntimeError("no template")
        w.events.append(("clone", kw["vm_name"]))
        w.vm_exists = True

    monkeypatch.setattr(ova_staging, "deploy_from_template", deploy_from_template)

    class FakeVc:
        def get_vm(self, name):
            return SimpleNamespace(name=name) if w.vm_exists else None

        def set_extra_config(self, vm, values):
            w.events.append(("extra_config", vm.name, dict(values)))

    @contextmanager
    def auth(cls, zpod):
        w.events.append(("auth",))
        yield FakeVc()

    monkeypatch.setattr(ovfdeployer.vCenter, "auth_by_zpod_endpoint", classmethod(auth))
    monkeypatch.setattr(ovfdeployer.vCenter, "auth_by_zpod", classmethod(auth))

    # The govc options file goes to /tmp/<fqdn>.json; keep it in the test's tmp dir.
    real_open = open

    def tmp_open(path, *a, **kw):
        if isinstance(path, str) and path.startswith("/tmp/"):
            path = str(tmp_path / path.removeprefix("/tmp/"))
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", tmp_open)
    return w


def zpod_component(extra=None):
    component_json = {
        "component_name": "ubuntu",
        "component_deploy_govc_spec": GOVC_SPEC,
        "component_isnested": False,
    }
    if extra is not None:
        component_json["component_deploy_extra_config"] = extra
    zpod = SimpleNamespace(
        name="lab",
        domain="lab.zpod.example",
        password="secret",
        endpoint=SimpleNamespace(
            endpoints={
                "compute": {
                    "hostname": "vcsa.example",
                    "username": "admin",
                    "password": "pw",
                    "datacenter": "DC",
                    "storage_datastore": "ds01",
                }
            }
        ),
    )
    component = SimpleNamespace(
        component_name="ubuntu",
        component_version="24.04",
        component_uid="ubuntu-24.04",
        filename="ubuntu.ova",
        component_json=component_json,
    )
    return SimpleNamespace(
        component=component,
        zpod=zpod,
        hostname="node1",
        fqdn="node1.lab.zpod.example",
        ip="10.42.111.30",
    )


def extra_event(world):
    (event,) = [e for e in world.events if e[0] == "extra_config"]
    return event


def test_without_extra_config_nothing_changes(world):
    ovfdeployer.ovf_deployer(zpod_component())
    # PowerOn stays what the library JSON says; no reconfigure, no vCenter login.
    assert world.events == [("import", True)]


def test_direct_import_powered_off_then_extra_config(world):
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["import", "auth", "extra_config"]
    assert world.events[0] == ("import", False)
    _, vm_name, values = extra_event(world)
    assert vm_name == "node1.lab.zpod.example"
    assert set(values) == {"guestinfo.metadata", "guestinfo.metadata.encoding"}


def test_staging_clone_then_extra_config(world):
    world.staging = "ok"
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["clone", "auth", "extra_config"]


def test_staging_failure_falls_back_to_import_then_extra_config(world):
    world.staging = "fail"
    ovfdeployer.ovf_deployer(zpod_component(EXTRA))
    assert [e[0] for e in world.events] == ["import", "auth", "extra_config"]
    assert world.events[0] == ("import", False)


def test_staging_without_extra_config_is_unchanged(world):
    world.staging = "ok"
    ovfdeployer.ovf_deployer(zpod_component())
    assert world.events == [("clone", "node1.lab.zpod.example")]


def test_bad_extra_config_fails_before_any_vm(world):
    with pytest.raises(ExtraConfigError):
        ovfdeployer.ovf_deployer(zpod_component({"disk.EnableUUID": "TRUE"}))
    assert world.events == []
