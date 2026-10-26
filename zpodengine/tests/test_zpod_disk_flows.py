"""The three disk flows end to end, in-process: the real vCenter disk helpers on a
fake VM (pyVmomi data objects, ReconfigVM_Task applied to its device list) and a
fake zboxapi that sees the VM's disks by serial, as zcore with disk.EnableUUID does.
"""

import itertools
import uuid as uuidlib
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from prefect.testing.utilities import prefect_test_harness
from pyVmomi import vim
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from zpodcommon import models as M
from zpodcommon.lib import vmware
from zpodengine.lib import database as engine_database
from zpodengine.lib import datastore_floor
from zpodengine.zpod_disk import common
from zpodengine.zpod_disk import flow_zpod_disk_add as add_mod
from zpodengine.zpod_disk import flow_zpod_disk_grow as grow_mod
from zpodengine.zpod_disk import flow_zpod_disk_remove as remove_mod

GIB = 1024**3
CALLS: list = []


def vdisk(key, unit, size_gb):
    d = vim.vm.device.VirtualDisk(
        key=key, controllerKey=1000, unitNumber=unit, capacityInBytes=size_gb * GIB
    )
    d.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
        uuid=str(uuidlib.uuid4()).upper()
    )
    return d


class FakeVM:
    def __init__(self):
        self.name = "zcore.demo.example.com"
        controller = vim.vm.device.ParaVirtualSCSIController(
            key=1000, controllerKey=100, unitNumber=0
        )
        self.devices = [controller, vdisk(2000, 0, 50), vdisk(2001, 1, 1024)]
        self.extra = [vim.option.OptionValue(key="disk.EnableUUID", value="TRUE")]
        self.next_key = itertools.count(2002)

    @property
    def config(self):
        return SimpleNamespace(
            hardware=SimpleNamespace(device=list(self.devices)),
            extraConfig=self.extra,
        )

    def ReconfigVM_Task(self, spec):
        for change in spec.deviceChange or []:
            CALLS.append(("vcenter", change.operation, change.device.unitNumber))
            if change.operation == "add":
                d = change.device
                d.key = next(self.next_key)
                d.backing.uuid = str(uuidlib.uuid4()).upper()
                self.devices.append(d)
            elif change.operation == "remove":
                self.devices = [d for d in self.devices if d.key != change.device.key]
        for option in spec.extraConfig or []:
            self.extra.append(option)
        return "task"


class FakeVC(vmware.vCenter):
    def __init__(self):  # no connection
        pass

    def vm_datastore(self, vm):
        return SimpleNamespace(name="ds01")


class Resp:
    def __init__(self, payload, status_code=200, method="GET", url="/"):
        self.payload, self.status_code = payload, status_code
        self.request = SimpleNamespace(method=method, url=SimpleNamespace(path=url))
        self.text = str(payload)

    def json(self):
        return self.payload


class FakeZcore:
    """zboxapi: every disk of the VM, by serial; `in_use` marks a disk mounted."""

    vm: FakeVM = None
    in_use: set = set()
    serials = True
    detached: set = set()

    def disks(self):
        out = []
        for i, d in enumerate(
            d for d in self.vm.devices if isinstance(d, vim.vm.device.VirtualDisk)
        ):
            serial = M.normalise_disk_uuid(d.backing.uuid)
            if serial in FakeZcore.detached:
                continue
            state = {0: "system", 1: "protected"}.get(d.unitNumber, "blank")
            if serial in FakeZcore.in_use:
                state = "in-use"
            out.append(
                {
                    "name": f"sd{'abcdefgh'[i]}",
                    "size_bytes": d.capacityInBytes,
                    "serial": serial if FakeZcore.serials else None,
                    "state": state,
                    "storage": "STORAGE02" if state == "in-use" else None,
                }
            )
        return out

    def get(self, url):
        CALLS.append(("zbox", "GET", url))
        if url == "/openapi.json":
            return Resp({"info": {"version": "0.2.1"}})
        return Resp(self.disks(), url=url)

    def post(self, url, json=None):
        CALLS.append(("zbox", "POST", url))
        if url == "/disk/rescan":
            return Resp({"new": [], "resized": [], "disks": self.disks()}, url=url)
        name = url.split("/")[2]
        for d in self.disks():
            if d["name"] == name:
                FakeZcore.detached.add(d["serial"])
        return Resp({"detached": True}, url=url)


@pytest.fixture(scope="module")
def prefect():
    with prefect_test_harness():
        yield


@pytest.fixture
def world(monkeypatch, prefect):
    CALLS.clear()
    vm = FakeVM()
    FakeZcore.vm, FakeZcore.in_use, FakeZcore.serials = vm, set(), True
    FakeZcore.detached = set()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def ctx():
        with Session(engine) as session:
            yield session

    @contextmanager
    def fake_zcore_vm(zpod):
        yield FakeVC(), vm

    monkeypatch.setattr(engine_database, "get_session_ctx", ctx)
    for mod in (common, add_mod, grow_mod, remove_mod):
        if hasattr(mod, "zcore_vm"):
            monkeypatch.setattr(mod, "zcore_vm", fake_zcore_vm)
    monkeypatch.setattr(
        common.ZboxApiClient, "by_zpod", staticmethod(lambda zpod: FakeZcore())
    )
    monkeypatch.setattr(vmware.task, "WaitForTask", lambda t: None)
    space = {"capacity": 10000 * GIB, "free": 5000 * GIB}
    monkeypatch.setattr(
        datastore_floor.vCenter,
        "datastore_space",
        staticmethod(lambda ds: (space["capacity"], space["free"])),
    )
    monkeypatch.setattr(
        datastore_floor.DBUtils, "get_setting_value", classmethod(lambda c, n: "15")
    )
    with Session(engine) as session:
        endpoint = M.Endpoint(name="ep", endpoints={}, status="ACTIVE")
        session.add(endpoint)
        session.flush()
        zpod = M.Zpod(
            name="demo",
            domain="demo.example.com",
            endpoint_id=endpoint.id,
            profile="p",
            status="ACTIVE",
            password="pw",
        )
        session.add(zpod)
        session.commit()
        zpod_id = zpod.id
    return SimpleNamespace(engine=engine, vm=vm, zpod_id=zpod_id, space=space)


def new_row(world, **kw) -> int:
    with Session(world.engine) as session:
        row = M.ZpodDisk(zpod_id=world.zpod_id, **kw)
        session.add(row)
        session.commit()
        return row.id


def rows(world):
    with Session(world.engine) as session:
        return [
            (r.kind, r.status, r.scsi_unit, r.vm_disk_key, r.size_gb)
            for r in session.query(M.ZpodDisk).order_by(M.ZpodDisk.scsi_unit)
        ]


def add(world, size_gb=500):
    disk_id = new_row(world, size_gb=size_gb, status="PENDING", kind="user")
    return disk_id, add_mod.flow_zpod_disk_add(
        zpod_id=world.zpod_id,
        disk_id=disk_id,
        zpod_name="demo",
        size_gb=size_gb,
        requested_by="timo",
        return_state=True,
    )


def test_add_records_the_deploy_disks_and_finds_the_new_one_by_serial(world):
    disk_id, state = add(world)
    assert state.is_completed(), state.message
    assert state.result() == "sdc"
    assert rows(world) == [
        ("zpod", "ACTIVE", 0, 2000, 50),
        ("zpod", "ACTIVE", 1, 2001, 1024),
        ("user", "ACTIVE", 2, 2002, 500),
    ]
    assert ("vcenter", "add", 2) in CALLS
    # zboxapi's version first, before vSphere is touched
    assert CALLS[0] == ("zbox", "GET", "/openapi.json")


def test_add_under_the_datastore_floor_creates_nothing(world):
    world.space["free"] = 1600 * GIB  # 800 more would leave 8%
    disk_id, state = add(world, 800)
    assert state.is_failed()
    assert "under the floor of 15%" in state.message
    assert not any(c[0] == "vcenter" for c in CALLS)
    assert [r for r in rows(world) if r[0] == "user"] == []


def test_add_without_serials_removes_the_disk_and_the_row(world):
    FakeZcore.serials = False
    disk_id, state = add(world)
    assert state.is_failed()
    assert "power-cycle it once" in state.message
    assert ("vcenter", "remove", 2) in CALLS
    assert [r for r in rows(world) if r[0] == "user"] == []
    assert len(world.vm.devices) == 3


def test_add_sets_enable_uuid_when_missing(world):
    world.vm.extra.clear()
    disk_id, state = add(world)
    assert any(o.key == "disk.EnableUUID" for o in world.vm.extra)


def test_grow_by_key_and_uuid(world):
    disk_id, _ = add(world)
    with Session(world.engine) as session:
        session.get(M.ZpodDisk, disk_id).status = "PENDING"
        session.commit()
    state = grow_mod.flow_zpod_disk_grow(
        zpod_id=world.zpod_id,
        disk_id=disk_id,
        size_gb=1000,
        zpod_name="demo",
        device="sdc",
        requested_by="timo",
        return_state=True,
    )
    assert state.is_completed(), state.message
    assert rows(world)[-1] == ("user", "ACTIVE", 2, 2002, 1000)


def test_grow_refuses_a_reused_key(world):
    """vCenter gave the key of a removed disk to another one: never grow it."""
    disk_id, _ = add(world)
    with Session(world.engine) as session:
        row = session.get(M.ZpodDisk, disk_id)
        row.vm_disk_key, row.status = 2001, "PENDING"
        session.commit()
    state = grow_mod.flow_zpod_disk_grow(
        zpod_id=world.zpod_id,
        disk_id=disk_id,
        size_gb=1000,
        zpod_name="demo",
        device="sdc",
        requested_by="timo",
        return_state=True,
    )
    assert state.is_failed()
    assert "expected 2001" in state.message
    assert rows(world)[-1][1] == "ACTIVE"  # the hook put it back


def remove(world, disk_id):
    with Session(world.engine) as session:
        session.get(M.ZpodDisk, disk_id).status = "PENDING"
        session.commit()
    return remove_mod.flow_zpod_disk_remove(
        zpod_id=world.zpod_id,
        disk_id=disk_id,
        zpod_name="demo",
        device="sdc",
        requested_by="timo",
        return_state=True,
    )


def test_remove_detaches_then_deletes(world):
    disk_id, _ = add(world)
    CALLS.clear()
    state = remove(world, disk_id)
    assert state.is_completed(), state.message
    order = [c for c in CALLS if c[1] in ("POST", "remove")]
    assert order == [("zbox", "POST", "/disk/sdc/detach"), ("vcenter", "remove", 2)]
    assert [r[0] for r in rows(world)] == ["zpod", "zpod"]


def test_remove_refuses_a_disk_in_use(world):
    disk_id, _ = add(world)
    with Session(world.engine) as session:
        FakeZcore.in_use = {session.get(M.ZpodDisk, disk_id).disk_uuid}
    state = remove(world, disk_id)
    assert state.is_failed()
    assert "in-use by STORAGE02" in state.message
    assert rows(world)[-1][:2] == ("user", "ACTIVE")
    assert len(world.vm.devices) == 4


def test_floor_check_logs_and_passes(world):
    disk_id, state = add(world, 100)
    assert state.is_completed()
