"""Virtual disks of a zPod's zcore: /zpods/{id}/disks.

zboxapi and the Prefect engine are faked; the rows are what the flows would write.
"""

import pytest
from fastapi import HTTPException

from zpodcommon import models as M

GIB = 1024**3
SDA = "6000c29f32f90e60544f3452a537d48a"
SDB = "6000c296b9409608688600707b6cc42c"
SDC = "6000c29a3b4ed72604fcc4dc737578fb"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload, self.status_code = payload, status_code

    def json(self):
        return self.payload

    def safejson(self):
        if self.status_code >= 400:
            raise HTTPException(status_code=self.status_code, detail=self.payload)
        return self.payload


def live(name, size_gb, serial, state, storage=None):
    return {
        "name": name,
        "path": f"/dev/{name}",
        "size_bytes": size_gb * GIB,
        "serial": serial,
        "state": state,
        "storage": storage,
    }


class FakeZcore:
    disks: list[dict] = []
    calls: list[tuple] = []

    @classmethod
    def reset(cls):
        cls.calls = []
        cls.disks = [
            live("sda", 50, SDA, "system"),
            live("sdb", 1024, SDB, "protected", "STORAGE01"),
        ]

    @classmethod
    def by_zpod(cls, zpod, **kwargs):
        return cls()

    def get(self, url, **kw):
        FakeZcore.calls.append(("GET", url))
        if url == "/openapi.json":
            return FakeResponse({"info": {"version": "0.2.1"}})
        if url == "/disk":
            return FakeResponse(list(FakeZcore.disks))
        raise AssertionError(url)


class FakeEngine:
    calls: list[dict] = []
    runs: dict[str, dict] = {}

    def create_flow_run_by_name(self, flow_name, deployment_name=None, **kw):
        FakeEngine.calls.append({"flow_name": flow_name, **kw})
        run_id = f"run-{len(FakeEngine.calls)}"
        params = {k: v for k, v in kw.items() if k != "run_name"}
        FakeEngine.runs[run_id] = {
            "id": run_id,
            "name": kw.get("run_name"),
            "state": "SCHEDULED",
            "message": None,
            "parameters": params,
        }
        return {"id": run_id}

    def get_flow_run(self, flow_run_id):
        return FakeEngine.runs.get(flow_run_id)


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    FakeZcore.reset()
    FakeEngine.calls, FakeEngine.runs = [], {}
    settings = {"zpodfactory_zpod_disk_max_gb": "2048"}
    monkeypatch.setattr("zpodapi.zpods.zpod_zcore.ZboxApiClient", FakeZcore)
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_disk__services.ZpodEngineClient", FakeEngine
    )
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_disk__services.DBUtils.get_setting_value",
        classmethod(lambda cls, name: settings.get(name)),
    )
    return settings


URL = "/zpods/name=lab/disks"


def add_row(session, lab, **kw):
    row = M.ZpodDisk(zpod_id=lab.id, **kw)
    session.add(row)
    session.commit()
    return row


def with_user_disk(session, lab, state="blank", storage=None):
    """sdc added by a flow: its row ACTIVE, zcore sees it."""
    FakeZcore.disks.append(live("sdc", 500, SDC, state, storage))
    return add_row(
        session,
        lab,
        kind="user",
        status="ACTIVE",
        size_gb=500,
        scsi_unit=2,
        vm_disk_key=2002,
        disk_uuid=SDC,
    )


# ── list ──────────────────────────────────────────────────────────────────────


def test_list_before_any_row_shows_the_deploy_disks(normaluser_client, lab):
    r = normaluser_client.get(URL)
    assert r.status_code == 200, r.text
    assert [(d["device"], d["state"], d["kind"], d["status"]) for d in r.json()] == [
        ("/dev/sda", "system", "zpod", "ACTIVE"),
        ("/dev/sdb", "protected", "zpod", "ACTIVE"),
    ]


def test_list_matches_rows_by_serial_and_derives_missing(
    normaluser_client, lab, session
):
    with_user_disk(session, lab)
    add_row(
        session,
        lab,
        kind="user",
        status="ACTIVE",
        size_gb=300,
        scsi_unit=3,
        vm_disk_key=2003,
        disk_uuid="6000c29d" + "0" * 24,
    )
    r = normaluser_client.get(URL)
    got = [(d["device"], d["scsi"], d["size_gb"], d["status"]) for d in r.json()]
    assert got == [
        ("/dev/sdc", "0:2", 500, "ACTIVE"),
        (None, "0:3", 300, "MISSING"),
        ("/dev/sda", None, 50, "ACTIVE"),
        ("/dev/sdb", None, 1024, "ACTIVE"),
    ]


def test_list_with_zcore_not_answering_is_unknown(
    normaluser_client, lab, session, monkeypatch
):
    with_user_disk(session, lab)
    from zpodcommon.lib.zboxapi import RequestError

    def down(cls, zpod, **kw):
        raise RequestError("timed out")

    monkeypatch.setattr(FakeZcore, "by_zpod", classmethod(down))
    r = normaluser_client.get(URL)
    assert r.status_code == 200, r.text
    assert [(d["device"], d["status"]) for d in r.json()] == [(None, "UNKNOWN")]


# ── add ───────────────────────────────────────────────────────────────────────


def test_add_writes_a_pending_row_and_starts_the_flow(normaluser_client, lab, session):
    r = normaluser_client.post(URL, json={"size_gb": 500})
    assert r.status_code == 202, r.text
    assert r.json()["disk"]["status"] == "PENDING"
    assert r.json()["flow_run_id"] == "run-1"
    call = FakeEngine.calls[0]
    assert call["flow_name"] == "zpod_disk_add"
    assert call["run_name"] == "add disk lab/500GiB by normaluser"
    row = session.get(M.ZpodDisk, call["disk_id"])
    assert (row.kind, row.status, row.size_gb) == ("user", "PENDING", 500)


def test_add_above_the_cap_is_422_but_not_for_superadmin(normaluser_client, lab, fakes):
    r = normaluser_client.post(URL, json={"size_gb": 5000})
    assert r.status_code == 422, r.text
    assert "above the limit of 2048 GiB" in r.json()["detail"]
    assert FakeEngine.calls == []
    normaluser_client.headers["access_token"] = "APITOKEN_SUPERUSER"
    assert normaluser_client.post(URL, json={"size_gb": 5000}).status_code == 202


def test_one_disk_change_at_a_time(normaluser_client, lab, session):
    add_row(session, lab, kind="user", status="PENDING", size_gb=10)
    r = normaluser_client.post(URL, json={"size_gb": 200})
    assert r.status_code == 409, r.text
    assert "one at a time per zPod" in r.json()["detail"]


def test_add_on_an_old_zboxapi_is_501(normaluser_client, lab, monkeypatch):
    def old(self, url, **kw):
        return FakeResponse({"info": {"version": "0.2.0"}})

    monkeypatch.setattr(FakeZcore, "get", old)
    r = normaluser_client.post(URL, json={"size_gb": 500})
    assert r.status_code == 501, r.text
    assert FakeEngine.calls == []


# ── grow ──────────────────────────────────────────────────────────────────────


def test_grow_a_user_disk(normaluser_client, lab, session):
    row = with_user_disk(session, lab)
    r = normaluser_client.put(f"{URL}/sdc/grow", json={"size_gb": 1000})
    assert r.status_code == 202, r.text
    call = FakeEngine.calls[0]
    assert (call["flow_name"], call["disk_id"], call["size_gb"]) == (
        "zpod_disk_grow",
        row.id,
        1000,
    )
    session.refresh(row)
    assert row.status == "PENDING"


def test_grow_the_filer_disk_records_it(normaluser_client, lab, session):
    r = normaluser_client.put(f"{URL}/sdb/grow", json={"size_gb": 2048})
    assert r.status_code == 202, r.text
    row = session.get(M.ZpodDisk, FakeEngine.calls[0]["disk_id"])
    assert (row.kind, row.disk_uuid, row.status) == ("zpod", SDB, "PENDING")


@pytest.mark.parametrize(
    "device, size, code, text",
    [
        ("sda", 100, 403, "system disk"),
        ("sdb", 1024, 422, "a disk only grows"),
        ("sdz", 100, 404, "no disk /dev/sdz"),
    ],
)
def test_grow_refusals(normaluser_client, lab, device, size, code, text):
    r = normaluser_client.put(f"{URL}/{device}/grow", json={"size_gb": size})
    assert r.status_code == code, r.text
    assert text in r.json()["detail"]
    assert FakeEngine.calls == []


# ── remove ────────────────────────────────────────────────────────────────────


def test_remove_a_blank_user_disk(normaluser_client, lab, session):
    row = with_user_disk(session, lab)
    r = normaluser_client.delete(f"{URL}/sdc")
    assert r.status_code == 202, r.text
    assert FakeEngine.calls[0]["flow_name"] == "zpod_disk_remove"
    session.refresh(row)
    assert row.status == "PENDING"


def test_remove_refused_while_in_use(normaluser_client, lab, session):
    with_user_disk(session, lab, "in-use", "STORAGE02")
    r = normaluser_client.delete(f"{URL}/sdc")
    assert r.status_code == 409, r.text
    assert (
        r.json()["detail"]
        == "/dev/sdc is in-use by STORAGE02. Delete the storage first."
    )


@pytest.mark.parametrize(
    "device, text", [("sda", "system disk"), ("sdb", "filer disk")]
)
def test_the_deploy_disks_are_never_removed(normaluser_client, lab, device, text):
    r = normaluser_client.delete(f"{URL}/{device}")
    assert r.status_code == 403, r.text
    assert text in r.json()["detail"]


def test_a_disk_added_by_hand_is_not_removed(normaluser_client, lab):
    FakeZcore.disks.append(live("sdc", 10, SDC, "blank"))
    r = normaluser_client.delete(f"{URL}/sdc")
    assert r.status_code == 403, r.text
    assert "not added through zPodFactory" in r.json()["detail"]


# ── run ───────────────────────────────────────────────────────────────────────


def test_the_run_shows_the_disk_and_the_failure(normaluser_client, lab, session):
    r = normaluser_client.post(URL, json={"size_gb": 500})
    run_id = r.json()["flow_run_id"]
    run = FakeEngine.runs[run_id]
    run["state"] = "FAILED"
    run["message"] = (
        "Flow run encountered an exception: DatastoreFloorError: datastore ds01: ..."
    )
    r = normaluser_client.get(f"{URL}/runs/{run_id}")
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "FAILED"
    assert r.json()["message"] == "datastore ds01: ..."
    assert normaluser_client.get(f"{URL}/runs/nope").status_code == 404


def test_a_zpod_user_lists_but_does_not_change(client, lab, session):
    reader = M.User(
        username="reader",
        email="r@example.com",
        api_token="APITOKEN_READER",
        superadmin=False,
        status="ENABLED",
    )
    lab.permissions.append(M.ZpodPermission(permission="USER", users=[reader]))
    session.commit()
    client.headers["access_token"] = "APITOKEN_READER"
    assert client.get(URL).status_code == 200
    assert client.post(URL, json={"size_gb": 10}).status_code == 401
