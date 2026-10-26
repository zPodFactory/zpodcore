"""NFS exports of a zPod's zcore: /zpods/{id}/nfs, and the zboxapi gate (D19).

zboxapi is replaced by FakeZcore, which keeps the exports of STORAGE01 as zcore-init
writes them and answers like zboxapi 0.2.1 does.
"""

import pytest
from fastapi import HTTPException

from zpodcommon.lib.zboxapi import RequestError, version_tuple


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload, self.status_code = payload, status_code

    def json(self):
        return self.payload

    def safejson(self):
        if self.status_code >= 400:
            raise HTTPException(status_code=self.status_code, detail=self.payload)
        return self.payload


def export(path, clients, options="rw,no_subtree_check", owner="system", **kw):
    _, _, storage, folder = path.split("/")
    return {
        "path": path,
        "storage": storage,
        "folder": folder,
        "options": options,
        "clients": [{"client": c, "options": options} for c in clients],
        "owner": owner,
        "protected": kw.get("protected", False),
        "active": True,
        "folder_exists": True,
    }


class FakeZcore:
    """zboxapi's /nfs as zcore 13.7 answers it; `calls` records every request."""

    version = "0.2.1"
    unreachable = False
    exports: dict[str, dict] = {}
    calls: list[tuple] = []

    @classmethod
    def reset(cls):
        cls.version, cls.unreachable, cls.calls = "0.2.1", False, []
        cls.exports = {
            e["path"]: e
            for e in (
                export("/FILER/STORAGE01/NFS-01", ["10.60.60.0/26"], protected=True),
                export(
                    "/FILER/STORAGE01/NFS-VCD",
                    ["10.60.60.0/26"],
                    "rw,no_subtree_check,no_root_squash",
                ),
            )
        }

    @classmethod
    def by_zpod(cls, zpod, **kwargs):
        if cls.unreachable:
            raise RequestError("connection timed out")
        return cls()

    def get(self, url, **kw):
        return self._call("GET", url, **kw)

    def post(self, url, **kw):
        return self._call("POST", url, **kw)

    def put(self, url, **kw):
        return self._call("PUT", url, **kw)

    def delete(self, url, **kw):
        return self._call("DELETE", url, **kw)

    def _call(self, method, url, json=None, **kw):
        FakeZcore.calls.append((method, url, json))
        if url == "/openapi.json":
            return FakeResponse({"info": {"version": FakeZcore.version}})
        ex = FakeZcore.exports
        if method == "GET" and url == "/nfs":
            return FakeResponse(sorted(ex.values(), key=lambda e: e["path"]))
        if method == "GET" and url == "/nfs/status":
            return FakeResponse(
                {
                    "service": "active",
                    "enabled": True,
                    "versions": ["3", "4"],
                    "threads": 16,
                    "exports": len(ex),
                    "exports_in_files": len(ex),
                    "inactive_exports": [],
                    "clients": [
                        {
                            "client": "10.60.60.11",
                            "path": "/FILER/STORAGE01/NFS-01",
                            "version": "3",
                        }
                    ],
                }
            )
        if method == "POST" and url == "/nfs":
            if json["storage"] != "STORAGE01":
                return FakeResponse(f"Storage {json['storage']} is not mounted", 400)
            path = f"/FILER/{json['storage']}/{json['folder']}"
            if path in ex:
                return FakeResponse(f"{path} is already exported", 409)
            ex[path] = export(
                path,
                json["clients"],
                json.get("options") or "rw,no_subtree_check,no_root_squash",
                "user-defined",
            )
            return FakeResponse(ex[path])
        parts = url.split("/")  # '', 'nfs', storage, folder[, 'client'[, client...]]
        path = f"/FILER/{parts[2]}/{parts[3]}"
        current = ex.get(path)
        if current and current["owner"] == "system" and method != "GET":
            if current["protected"]:
                return FakeResponse(f"{path} is a protected export", 403)
            return FakeResponse(f"{path} is exported by /etc/exports", 403)
        if method == "GET":
            return FakeResponse(
                current or f"Export {path} not found", 200 if current else 404
            )
        if method == "PUT":
            created = current is None
            options = json.get("options") or (
                current["options"] if current else "rw,no_subtree_check,no_root_squash"
            )
            ex[path] = export(path, json["clients"], options, "user-defined")
            return FakeResponse(ex[path], 201 if created else 200)
        if current is None:
            return FakeResponse(f"Export {path} not found", 404)
        clients = [c["client"] for c in current["clients"]]
        if method == "POST":  # .../client
            if json["client"] in clients:
                return FakeResponse(f"{json['client']} is already a client", 409)
            ex[path] = export(
                path, [*clients, json["client"]], current["options"], "user-defined"
            )
            return FakeResponse(ex[path])
        if len(parts) > 4:  # DELETE .../client/<client, maybe with a slash>
            client = "/".join(parts[5:])
            clients.remove(client)
            if not clients:
                del ex[path]
                return FakeResponse(
                    {"message": "last client", "path": path, "folder_kept": True}
                )
            ex[path] = export(path, clients, current["options"], "user-defined")
            return FakeResponse(ex[path])
        del ex[path]
        return FakeResponse(
            {"message": "unexported", "path": path, "folder_kept": True}
        )


@pytest.fixture(autouse=True)
def fake_zcore(monkeypatch):
    FakeZcore.reset()
    monkeypatch.setattr("zpodapi.zpods.zpod_zcore.ZboxApiClient", FakeZcore)
    return FakeZcore


URL = "/zpods/name=lab/nfs"


def zbox_calls():
    return [(m, u) for m, u, _ in FakeZcore.calls if u != "/openapi.json"]


# ── reads ─────────────────────────────────────────────────────────────────────


def test_list_is_what_zboxapi_reports(normaluser_client, lab):
    r = normaluser_client.get(URL)
    assert r.status_code == 200, r.text
    assert [(e["path"], e["owner"], e["protected"]) for e in r.json()] == [
        ("/FILER/STORAGE01/NFS-01", "system", True),
        ("/FILER/STORAGE01/NFS-VCD", "system", False),
    ]


def test_status_lists_the_mounted_clients(normaluser_client, lab):
    r = normaluser_client.get(f"{URL}/status")
    assert r.status_code == 200, r.text
    assert r.json()["clients"][0]["client"] == "10.60.60.11"


def test_get_one_export_and_404(normaluser_client, lab):
    assert normaluser_client.get(f"{URL}/STORAGE01/NFS-01").status_code == 200
    assert normaluser_client.get(f"{URL}/STORAGE01/NOPE").status_code == 404


# ── changes ───────────────────────────────────────────────────────────────────


def test_add_defaults_the_clients_to_everyone(normaluser_client, lab):
    r = normaluser_client.post(URL, json={"storage": "STORAGE01", "folder": "ISO"})
    assert r.status_code == 201, r.text
    assert [c["client"] for c in r.json()["clients"]] == ["*"]
    assert FakeZcore.calls[-1][2] == {
        "storage": "STORAGE01",
        "folder": "ISO",
        "clients": ["*"],
    }


def test_add_with_clients_and_options(normaluser_client, lab):
    r = normaluser_client.post(
        URL,
        json={
            "storage": "STORAGE01",
            "folder": "ISO",
            "clients": ["10.42.111.0/24"],
            "options": "ro,no_subtree_check",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["options"] == "ro,no_subtree_check"


@pytest.mark.parametrize("clients", [["bogus"], [], ["10.42.111.300"]])
def test_add_refuses_a_bad_client_before_zboxapi(normaluser_client, lab, clients):
    r = normaluser_client.post(
        URL, json={"storage": "STORAGE01", "folder": "ISO", "clients": clients}
    )
    assert r.status_code == 422, r.text
    assert zbox_calls() == []


def test_zboxapi_refusals_pass_through(normaluser_client, lab):
    r = normaluser_client.post(URL, json={"storage": "STORAGE09", "folder": "X"})
    assert (r.status_code, r.json()["detail"]) == (
        400,
        "Storage STORAGE09 is not mounted",
    )
    assert normaluser_client.delete(f"{URL}/STORAGE01/NFS-01").status_code == 403
    r = normaluser_client.post(
        f"{URL}/STORAGE01/NFS-VCD/clients", json={"client": "172.16.42.0/24"}
    )
    assert r.status_code == 403


def test_client_add_and_remove_a_cidr(normaluser_client, lab):
    normaluser_client.post(URL, json={"storage": "STORAGE01", "folder": "ISO"})
    r = normaluser_client.post(
        f"{URL}/STORAGE01/ISO/clients", json={"client": "10.42.111.0/24"}
    )
    assert [c["client"] for c in r.json()["clients"]] == ["*", "10.42.111.0/24"]
    r = normaluser_client.delete(f"{URL}/STORAGE01/ISO/clients/*")
    assert [c["client"] for c in r.json()["clients"]] == ["10.42.111.0/24"]
    # the CIDR's slash, encoded or not, reaches zboxapi as part of the client
    r = normaluser_client.delete(f"{URL}/STORAGE01/ISO/clients/10.42.111.0%2F24")
    assert r.status_code == 200, r.text
    assert r.json()["folder_kept"] is True
    assert ("DELETE", "/nfs/STORAGE01/ISO/client/10.42.111.0/24") in zbox_calls()


def test_set_answers_201_when_created_and_200_when_replaced(normaluser_client, lab):
    body = {"clients": ["10.42.112.0/24"]}
    r = normaluser_client.put(f"{URL}/STORAGE01/BACKUPS", json=body)
    assert r.status_code == 201, r.text
    body = {"clients": ["10.42.112.0/24"], "options": "rw,no_subtree_check,root_squash"}
    r = normaluser_client.put(f"{URL}/STORAGE01/BACKUPS", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["options"] == "rw,no_subtree_check,root_squash"


def test_remove_keeps_the_folder(normaluser_client, lab):
    normaluser_client.post(URL, json={"storage": "STORAGE01", "folder": "ISO"})
    r = normaluser_client.delete(f"{URL}/STORAGE01/ISO")
    assert r.status_code == 200, r.text
    assert r.json()["folder_kept"] is True


# ── permissions and the gate ─────────────────────────────────────────────────


def test_a_zpod_user_reads_but_does_not_change(client, lab, session):
    from zpodcommon import models as M

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
    r = client.post(URL, json={"storage": "STORAGE01", "folder": "ISO"})
    assert r.status_code == 401, r.text
    assert ("POST", "/nfs") not in zbox_calls()


def test_a_stranger_does_not_see_the_zpod(client, lab, session):
    from zpodcommon import models as M

    session.add(
        M.User(
            username="stranger",
            email="s@example.com",
            api_token="APITOKEN_STRANGER",
            superadmin=False,
            status="ENABLED",
        )
    )
    session.commit()
    client.headers["access_token"] = "APITOKEN_STRANGER"
    assert client.get(URL).status_code == 404
    assert FakeZcore.calls == []


@pytest.mark.parametrize("version", ["0.2.0", "0.1.1", "unknown", "garbled"])
def test_zboxapi_below_0_2_1_answers_501(normaluser_client, lab, version):
    FakeZcore.version = version
    r = normaluser_client.get(URL)
    assert r.status_code == 501, r.text
    assert r.json()["detail"] == (
        f"zPod lab runs zboxapi {version}; storage needs ≥ 0.2.1 (zcore ≥ 13.7)."
    )
    assert zbox_calls() == []


def test_a_newer_zboxapi_passes(normaluser_client, lab):
    FakeZcore.version = "0.3.0.dev2"
    assert normaluser_client.get(URL).status_code == 200


def test_zcore_not_answering_is_503(normaluser_client, lab):
    FakeZcore.unreachable = True
    r = normaluser_client.get(URL)
    assert r.status_code == 503, r.text
    assert "zcore.lab.example.com does not answer" in r.json()["detail"]


def test_zcore_not_active_is_409(normaluser_client, lab, session):
    lab.components[0].status = "BUILDING"
    session.commit()
    r = normaluser_client.post(URL, json={"storage": "STORAGE01", "folder": "ISO"})
    assert r.status_code == 409, r.text
    assert FakeZcore.calls == []


def test_version_tuple():
    assert version_tuple("0.2.1") == (0, 2, 1)
    assert version_tuple("0.2.1.dev3") == (0, 2, 1)
    assert version_tuple("1.10.0+local") == (1, 10, 0)
    assert version_tuple("unknown") is None
    assert version_tuple("0.2") is None
