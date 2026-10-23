"""Storages of a zPod's zcore: /zpods/{id}/storages, forwarded to zboxapi.

zboxapi is faked; what zpodapi adds is checked: the kind, the ownership of a disk
to format or adopt, the query flags, the gate.
"""

import pytest
from fastapi import HTTPException

from zpodcommon import models as M

SDB = "6000c296b9409608688600707b6cc42c"
SDC = "6000c29a3b4ed72604fcc4dc737578fb"
SDD = "6000c29d0000000000000000000000dd"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload, self.status_code = payload, status_code

    def json(self):
        return self.payload

    def safejson(self):
        if self.status_code >= 400:
            raise HTTPException(status_code=self.status_code, detail=self.payload)
        return self.payload


def storage(name, disk, protected=False, managed=True):
    return {
        "name": name,
        "mountpoint": f"/FILER/{name}",
        "disk": disk,
        "device": f"/dev/{disk}1",
        "layout": "raw",
        "vg": None,
        "lv": None,
        "fstype": "ext4",
        "uuid": "u",
        "size_bytes": 500 * 1024**3,
        "used_bytes": 1024**3,
        "available_bytes": 499 * 1024**3,
        "protected": protected,
        "managed": managed,
        "exports": 0,
        "folders": [],
    }


class FakeZcore:
    calls: list[tuple] = []

    @classmethod
    def by_zpod(cls, zpod, **kwargs):
        return cls()

    def _call(self, method, url, json=None, params=None):
        FakeZcore.calls.append((method, url, json, params))
        if url == "/openapi.json":
            return FakeResponse({"info": {"version": "0.2.1"}})
        if method == "GET" and url == "/storage":
            return FakeResponse(
                [
                    storage("STORAGE01", "sdb", protected=True, managed=False),
                    storage("STORAGE02", "sdc"),
                ]
            )
        if method == "GET" and url.startswith("/disk/"):
            name = url.split("/")[2]
            serial = {"sdb": SDB, "sdc": SDC, "sdd": SDD}.get(name)
            return FakeResponse({"name": name, "serial": serial, "state": "blank"})
        if url.startswith("/storage") and method in ("POST", "DELETE", "PUT"):
            if url.count("/") == 3 and not url.endswith("/grow"):  # a folder
                return FakeResponse(
                    {
                        "name": url.split("/")[3],
                        "path": "/FILER/x",
                        "exported": False,
                        "protected": False,
                        "empty": True,
                        "mode": "0777",
                        "owner": "root:root",
                        "message": "removed",
                        "removed": 1,
                        "forced": bool(params and params.get("force") == "true"),
                    }
                )
            return FakeResponse(
                {
                    "operation": "create",
                    "name": "STORAGE02",
                    "dry_run": (params or {}).get("dry_run") == "true",
                    "storage": storage("STORAGE02", "sdc"),
                    "steps": [{"step": "mkfs", "target": "sdc1", "status": "done"}],
                }
            )
        raise AssertionError(f"{method} {url}")

    def get(self, url, **kw):
        return self._call("GET", url, **kw)

    def post(self, url, **kw):
        return self._call("POST", url, **kw)

    def put(self, url, **kw):
        return self._call("PUT", url, **kw)

    def delete(self, url, **kw):
        return self._call("DELETE", url, **kw)


@pytest.fixture(autouse=True)
def fake_zcore(monkeypatch):
    FakeZcore.calls = []
    monkeypatch.setattr("zpodapi.zpods.zpod_zcore.ZboxApiClient", FakeZcore)


@pytest.fixture
def lab_disks(session, lab):
    """sdb (the filer disk) and sdc (a user disk) are the zPod's; sdd is not."""
    for kind, unit, uuid in (("zpod", 1, SDB), ("user", 2, SDC)):
        session.add(
            M.ZpodDisk(
                zpod_id=lab.id,
                kind=kind,
                status="ACTIVE",
                size_gb=500,
                scsi_unit=unit,
                disk_uuid=uuid,
            )
        )
    session.commit()
    return lab


URL = "/zpods/name=lab/storages"


def zbox_changes():
    return [c for c in FakeZcore.calls if c[0] != "GET"]


def test_list_marks_storage01_as_zcore(normaluser_client, lab):
    r = normaluser_client.get(URL)
    assert r.status_code == 200, r.text
    assert [(s["name"], s["kind"]) for s in r.json()] == [
        ("STORAGE01", "zcore"),
        ("STORAGE02", "user"),
    ]


def test_create_on_a_disk_of_the_zpod(normaluser_client, lab_disks):
    r = normaluser_client.post(f"{URL}?dry_run=true", json={"disk": "/dev/sdc"})
    assert r.status_code == 201, r.text
    assert r.json()["dry_run"] is True
    assert r.json()["storage"]["kind"] == "user"
    assert zbox_changes() == [
        (
            "POST",
            "/storage",
            {"disk": "sdc", "lvm": False},
            {"dry_run": "true", "verbose": "false"},
        )
    ]


def test_create_with_lvm_and_a_name(normaluser_client, lab_disks):
    r = normaluser_client.post(
        URL, json={"disk": "sdc", "lvm": True, "name": "STORAGE07"}
    )
    assert r.status_code == 201, r.text
    assert zbox_changes()[0][2] == {"disk": "sdc", "lvm": True, "name": "STORAGE07"}


def test_create_refuses_a_disk_that_is_not_the_zpods(normaluser_client, lab_disks):
    r = normaluser_client.post(URL, json={"disk": "/dev/sdd"})
    assert r.status_code == 403, r.text
    assert "/dev/sdd is not one of zPod lab's disks" in r.json()["detail"]
    assert zbox_changes() == []


def test_adopt_checks_the_disk_of_a_partition(normaluser_client, lab_disks):
    assert (
        normaluser_client.post(f"{URL}/adopt", json={"device": "/dev/sdd1"}).status_code
        == 403
    )
    r = normaluser_client.post(
        f"{URL}/adopt", json={"device": "/dev/sdc1", "name": "STORAGE02"}
    )
    assert r.status_code == 201, r.text
    assert zbox_changes()[-1][2] == {"device": "sdc1", "name": "STORAGE02"}


def test_grow_and_delete_are_forwarded(normaluser_client, lab):
    assert normaluser_client.put(f"{URL}/STORAGE02/grow").status_code == 200
    assert normaluser_client.delete(f"{URL}/STORAGE02?dry_run=true").status_code == 200
    assert [(m, u) for m, u, _, _ in zbox_changes()] == [
        ("POST", "/storage/STORAGE02/grow"),
        ("DELETE", "/storage/STORAGE02"),
    ]


def test_folders(normaluser_client, lab):
    r = normaluser_client.post(
        f"{URL}/STORAGE02/folders/DATASTORE01", json={"mode": "0755"}
    )
    assert r.status_code == 201, r.text
    r = normaluser_client.put(
        f"{URL}/STORAGE02/folders/DATASTORE01",
        json={"owner": "1000:1000", "recursive": True},
    )
    assert r.status_code == 200, r.text
    r = normaluser_client.delete(f"{URL}/STORAGE02/folders/DATASTORE01?force=true")
    assert r.status_code == 200, r.text
    assert r.json()["forced"] is True
    assert [(m, u, j) for m, u, j, _ in zbox_changes()] == [
        ("POST", "/storage/STORAGE02/DATASTORE01", {"mode": "0755"}),
        (
            "PUT",
            "/storage/STORAGE02/DATASTORE01",
            {"owner": "1000:1000", "recursive": True},
        ),
        ("DELETE", "/storage/STORAGE02/DATASTORE01", None),
    ]


def test_old_zboxapi_is_501(normaluser_client, lab, monkeypatch):
    monkeypatch.setattr(
        FakeZcore,
        "get",
        lambda self, url, **kw: FakeResponse({"info": {"version": "0.2.0"}}),
    )
    assert normaluser_client.get(URL).status_code == 501
