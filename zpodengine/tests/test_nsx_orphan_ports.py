"""Classification, reporting and cleanup of orphan NSX segment ports."""

from types import SimpleNamespace

import pytest

from zpodengine.lib import nsx_orphan_ports as orphan

LIVE_HOST = "aaaaaaaa-live"
GHOST_HOST = "f580ee2f-ghost"
PFX = "[ff_nsx_clean_orphan_ports]"
TABLE_HEADER = (
    f"{PFX} VM & Orphan ports to delete "
    "(NSX inventory sync issue - Check with your NSX Admin)"
)


class FakeResponse:
    def __init__(self, payload=None, status_code=200, text=""):
        self._payload, self.status_code, self.text = payload or {}, status_code, text

    def safejson(self):
        return self._payload


class FakeNsx:
    """Serves canned answers; records every DELETE and can drop ports on delete."""

    def __init__(self, ports, vifs, vms, delete_status=200):
        self.ports, self.vifs, self.vms = ports, vifs, vms
        self.deleted, self.delete_status = [], delete_status

    def get(self, path, params=None):
        params = params or {}
        if path == "/api/v1/transport-nodes":
            return FakeResponse(
                {"results": [{"id": LIVE_HOST, "display_name": "esx-live"}]}
            )
        if path.endswith("/ports"):
            return FakeResponse({"results": self.ports})
        if path == "/api/v1/fabric/vifs":
            return FakeResponse(
                {"results": self.vifs.get(params["lport_attachment_id"], [])}
            )
        if path == "/api/v1/fabric/virtual-machines":
            return FakeResponse({"results": self.vms.get(params["external_id"], [])})
        raise AssertionError(f"unexpected NSX call {path} {params}")

    def delete(self, url):
        self.deleted.append(url)
        if self.delete_status < 300:
            self.ports = [p for p in self.ports if not url.endswith(p["id"])]
        return FakeResponse(status_code=self.delete_status, text="boom")


class FakeVc:
    def __init__(self, existing):
        self.existing = set(existing)

    def get_vm(self, name, **_):
        return SimpleNamespace(name=name) if name in self.existing else None


def port(pid, name, vif):
    return {
        "id": f"default:{pid}",
        "display_name": name,
        "path": f"/infra/segments/zpod-x-segment/ports/default:{pid}",
        "attachment": {"id": vif},
    }


SEGMENT = {"display_name": "zpod-x-segment", "path": "/infra/segments/zpod-x-segment"}
P1 = "/policy/api/v1/infra/segments/zpod-x-segment/ports/default:p1"
P2 = "/policy/api/v1/infra/segments/zpod-x-segment/ports/default:p2"


@pytest.fixture
def nsx():
    return FakeNsx(
        ports=[
            port("p1", "zcore.x.zpod.io.vmx@vif1", "vif1"),  # ghost host, VM gone
            port("p2", "esxi11.x.zpod.io.vmx@vif2", "vif2"),  # live host, VM gone
            port("p3", "hermes.y.zpod.io.vmx@vif3", "vif3"),  # ghost host, VM exists
            port("p4", "fine.x.zpod.io.vmx@vif4", "vif4"),  # live host, VM exists
            port("p5", "mystery", "vif5"),  # no VIF record at all
        ],
        vifs={
            "vif1": [{"owner_vm_id": "vm1"}],
            "vif2": [{"owner_vm_id": "vm2"}],
            "vif3": [{"owner_vm_id": "vm3"}],
            "vif4": [{"owner_vm_id": "vm4"}],
        },
        vms={
            "vm1": [
                {
                    "display_name": "zcore.x.zpod.io",
                    "external_id": "vm1",
                    "host_id": GHOST_HOST,
                }
            ],
            "vm2": [
                {
                    "display_name": "esxi11.x.zpod.io",
                    "external_id": "vm2",
                    "host_id": LIVE_HOST,
                }
            ],
            "vm3": [
                {
                    "display_name": "hermes.y.zpod.io",
                    "external_id": "vm3",
                    "host_id": GHOST_HOST,
                }
            ],
            "vm4": [
                {
                    "display_name": "fine.x.zpod.io",
                    "external_id": "vm4",
                    "host_id": LIVE_HOST,
                }
            ],
        },
    )


@pytest.fixture
def vc():
    return FakeVc(existing={"hermes.y.zpod.io", "fine.x.zpod.io"})


@pytest.fixture
def flag(monkeypatch):
    """Serve ff_nsx_clean_orphan_ports from a dict; 'true' unless a test says otherwise."""
    values = {orphan.FF_CLEAN_ORPHAN_PORTS: "true"}
    monkeypatch.setattr(
        orphan.DBUtils,
        "get_setting_value",
        classmethod(lambda cls, name: values.get(name)),
    )
    return values


@pytest.fixture
def zpod_and_vc(monkeypatch, vc, flag):
    """evacuate_segment opens vCenter from the zPod endpoint; stub that."""

    class _Ctx:
        def __enter__(self):
            return vc

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        orphan.vCenter, "auth_by_zpod_endpoint", classmethod(lambda cls, **k: _Ctx())
    )
    return SimpleNamespace(name="x")


def _fake_wait(calls):
    """wait_for_segment_to_be_evacuted stand-in: raise while ports remain."""

    def wait(nsx, segment, **_):
        calls.append(len(nsx.ports))
        if nsx.ports:
            raise ValueError("Failed: Segment has connected ports / interfaces.")

    return wait


def test_classify_matrix():
    c = orphan.classify
    assert c(has_vif=False, host_live=False, vm_in_vcenter=None) == orphan.NO_VIF
    assert (
        c(has_vif=True, host_live=False, vm_in_vcenter=False)
        == orphan.ORPHAN_GHOST_HOST
    )
    assert (
        c(has_vif=True, host_live=False, vm_in_vcenter=True) == orphan.STALE_INVENTORY
    )
    assert (
        c(has_vif=True, host_live=True, vm_in_vcenter=False) == orphan.ORPHAN_LIVE_HOST
    )
    assert c(has_vif=True, host_live=True, vm_in_vcenter=True) == orphan.OK
    # Without vCenter only host liveness can be judged, nothing is deletable
    assert (
        c(has_vif=True, host_live=False, vm_in_vcenter=None) == orphan.STALE_INVENTORY
    )
    assert c(has_vif=True, host_live=True, vm_in_vcenter=None) == orphan.OK


def test_audit_classifies_silently_and_deletes_nothing(nsx, vc, capsys):
    records = orphan.audit_segment_ports(nsx, SEGMENT, vc)
    by_name = {r["port_name"].split(".vmx@")[0]: r for r in records}

    assert by_name["zcore.x.zpod.io"]["verdict"] == orphan.ORPHAN_GHOST_HOST
    assert by_name["esxi11.x.zpod.io"]["verdict"] == orphan.ORPHAN_LIVE_HOST
    assert by_name["hermes.y.zpod.io"]["verdict"] == orphan.STALE_INVENTORY
    assert by_name["fine.x.zpod.io"]["verdict"] == orphan.OK
    assert by_name["mystery"]["verdict"] == orphan.NO_VIF
    assert [r["port_id"] for r in records if r["deletable"]] == [
        "default:p1",
        "default:p2",
    ]
    assert by_name["zcore.x.zpod.io"]["delete_path"] == P1
    assert nsx.deleted == []
    assert capsys.readouterr().out == ""


def test_audit_without_vcenter_marks_nothing_deletable(nsx):
    records = orphan.audit_segment_ports(nsx, SEGMENT, None)
    assert not any(r["deletable"] for r in records)
    assert all(r["vm_in_vcenter"] is None for r in records)


def test_format_reports(nsx, vc):
    records = orphan.audit_segment_ports(nsx, SEGMENT, vc)
    assert orphan.format_orphan_report(records) == (
        f"{TABLE_HEADER}\n- zcore.x.zpod.io (default:p1)\n- esxi11.x.zpod.io (default:p2)"
    )
    assert orphan.format_orphan_report([]) == f"{PFX} No orphan ports to delete."
    assert orphan.format_kept_report(records) == (
        f"{PFX} Ports kept, not orphan (VM still exists in vCenter, or could not be resolved)\n"
        "- hermes.y.zpod.io (default:p3) verdict=STALE\n"
        "- fine.x.zpod.io (default:p4) verdict=OK\n"
        "- mystery (default:p5) verdict=UNKNOWN"
    )
    assert orphan.format_kept_report([r for r in records if r["deletable"]]) == ""


def test_delete_orphan_ports_only_touches_deletable(nsx, vc, capsys):
    records = orphan.audit_segment_ports(nsx, SEGMENT, vc)
    deleted = orphan.delete_orphan_ports(nsx, records)
    assert [r["port_id"] for r in deleted] == ["default:p1", "default:p2"]
    assert nsx.deleted == [P1, P2]  # STALE / OK / UNKNOWN ports untouched
    assert {p["id"] for p in nsx.ports} == {"default:p3", "default:p4", "default:p5"}
    out = capsys.readouterr().out
    assert f"DELETE: {P1}" in out
    assert f"DELETE: {P2}" in out
    assert f"{PFX} deleted 2/2 orphan port(s)" in out


def test_delete_orphan_ports_reports_failures(nsx, vc, capsys):
    nsx.delete_status = 500
    records = orphan.audit_segment_ports(nsx, SEGMENT, vc)
    assert orphan.delete_orphan_ports(nsx, records) == []
    out = capsys.readouterr().out
    assert f"{PFX} failed to delete default:p1 (HTTP 500): boom" in out
    assert f"{PFX} deleted 0/2 orphan port(s)" in out


def test_evacuate_segment_normal_path_is_silent(monkeypatch, nsx, zpod_and_vc, capsys):
    nsx.ports = []
    calls = []
    monkeypatch.setattr(orphan, "wait_for_segment_to_be_evacuted", _fake_wait(calls))
    assert orphan.evacuate_segment(nsx, SEGMENT, zpod_and_vc) == []
    assert calls == [0] and nsx.deleted == []
    assert capsys.readouterr().out == ""  # nothing logged before / without a timeout


def test_evacuate_segment_cleans_orphans_then_rechecks(
    monkeypatch, nsx, zpod_and_vc, capsys
):
    # Only the two orphan ports remain after the vApp deletion.
    nsx.ports = [p for p in nsx.ports if p["id"] in ("default:p1", "default:p2")]
    calls = []
    monkeypatch.setattr(orphan, "wait_for_segment_to_be_evacuted", _fake_wait(calls))
    deleted = orphan.evacuate_segment(nsx, SEGMENT, zpod_and_vc)
    assert [r["port_id"] for r in deleted] == ["default:p1", "default:p2"]
    assert nsx.deleted == [P1, P2]
    assert calls == [2, 0]  # timed out once, clean after the cleanup
    out = capsys.readouterr().out
    # Straight to the table, then the flag state, then one DELETE per listed port
    assert out.startswith(TABLE_HEADER)
    assert "- zcore.x.zpod.io (default:p1)" in out
    assert "- esxi11.x.zpod.io (default:p2)" in out
    assert "Ports kept" not in out
    flag_at = out.index(f"{PFX} enabled=true -> deleting the orphan ports listed above")
    assert flag_at < out.index(f"DELETE: {P1}") < out.index(f"DELETE: {P2}")
    assert f"{PFX} deleted 2/2 orphan port(s)" in out


def test_evacuate_segment_lists_kept_ports_and_still_raises(
    monkeypatch, nsx, zpod_and_vc, capsys
):
    # A port whose VM still exists in vCenter must never be deleted.
    nsx.ports = [p for p in nsx.ports if p["id"] == "default:p3"]
    calls = []
    monkeypatch.setattr(orphan, "wait_for_segment_to_be_evacuted", _fake_wait(calls))
    with pytest.raises(ValueError, match="connected ports"):
        orphan.evacuate_segment(nsx, SEGMENT, zpod_and_vc)
    assert nsx.deleted == [] and calls == [1]
    out = capsys.readouterr().out
    assert f"{PFX} No orphan ports to delete." in out
    assert "- hermes.y.zpod.io (default:p3) verdict=STALE" in out


@pytest.mark.parametrize("value", [None, "", "false", "False", "0", "yes"])
def test_evacuate_segment_reports_only_when_flag_off(
    monkeypatch, nsx, zpod_and_vc, flag, value, capsys
):
    flag[orphan.FF_CLEAN_ORPHAN_PORTS] = value
    nsx.ports = [p for p in nsx.ports if p["id"] in ("default:p1", "default:p2")]
    calls = []
    monkeypatch.setattr(orphan, "wait_for_segment_to_be_evacuted", _fake_wait(calls))
    with pytest.raises(ValueError, match="connected ports"):
        orphan.evacuate_segment(nsx, SEGMENT, zpod_and_vc)
    assert nsx.deleted == [] and calls == [2]
    out = capsys.readouterr().out
    assert out.startswith(TABLE_HEADER)
    assert "- zcore.x.zpod.io (default:p1)" in out
    assert f"{PFX} enabled=false -> orphan ports reported only, nothing deleted" in out
    assert "DELETE:" not in out


@pytest.mark.parametrize(
    "value,enabled", [("true", True), (" TRUE ", True), ("false", False), (None, False)]
)
def test_clean_orphan_ports_enabled_parsing(flag, value, enabled):
    flag[orphan.FF_CLEAN_ORPHAN_PORTS] = value
    assert orphan.clean_orphan_ports_enabled() is enabled
