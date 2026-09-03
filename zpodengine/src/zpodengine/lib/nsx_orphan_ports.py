"""Detect and clean up orphan NSX segment ports during zpod destroy.

After the vApp is deleted, every VIF port on the zPod segment should vanish
within seconds. When NSX Manager's fabric inventory is stale (typically a
host that died and was removed from vCenter/NSX without its VMs being
re-homed), NSX still attributes the VIF to a ghost host, never receives the
"VIF removed" event, and the port stays forever. zpod_destroy then fails in
wait_for_segment_to_be_evacuted with "Segment has connected ports".

Flow (see evacuate_segment):
  1. wait for the segment to drain as before,
  2. only if that wait times out: classify the remaining ports, list the
     ones whose VM no longer exists in vCenter and, if the
     ff_nsx_clean_orphan_ports setting is "true", delete them and wait once
     more.
Ports whose VM still exists in vCenter are never deleted, whatever NSX says.
"""

from zpodcommon import models as M
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.nsx import NsxClient
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib.network import wait_for_segment_to_be_evacuted

# Feature flag: only when "true" are orphan ports actually deleted. Otherwise
# they are reported in the task log and the destroy fails as it always did.
FF_CLEAN_ORPHAN_PORTS = "ff_nsx_clean_orphan_ports"

# Every line this module logs is prefixed with the flag name, so the whole
# feature can be grepped out of the task logs with one pattern.
LOG_PREFIX = f"[{FF_CLEAN_ORPHAN_PORTS}]"

# Verdicts
OK = "OK"
ORPHAN_GHOST_HOST = "ORPHAN"  # NSX host is gone AND VM is gone from vCenter
ORPHAN_LIVE_HOST = "ORPHAN?"  # host is live but VM is gone (may still be settling)
STALE_INVENTORY = "STALE"  # NSX host is gone but the VM still exists in vCenter
NO_VIF = "UNKNOWN"  # port has no VIF record in the NSX fabric inventory

# Only ports whose VM is confirmed gone from vCenter may be deleted.
DELETE_VERDICTS = {ORPHAN_GHOST_HOST, ORPHAN_LIVE_HOST}


def _results(nsx: NsxClient, path: str, **params) -> list[dict]:
    return nsx.get(path, params=params).safejson().get("results", []) or []


def get_live_host_ids(nsx: NsxClient) -> dict[str, str]:
    """Transport nodes of type HostNode currently known to NSX: {id: name}."""
    return {
        tn["id"]: tn.get("display_name", tn["id"])
        for tn in _results(nsx, "/api/v1/transport-nodes", node_types="HostNode")
    }


def classify(*, has_vif: bool, host_live: bool, vm_in_vcenter: bool | None) -> str:
    """Pure classification of one port; vm_in_vcenter=None means 'not checked'."""
    if not has_vif:
        return NO_VIF
    if vm_in_vcenter is None:
        # No vCenter available: only the NSX host liveness can be judged, and
        # nothing is ever deletable without the vCenter confirmation.
        return STALE_INVENTORY if not host_live else OK
    if not host_live and not vm_in_vcenter:
        return ORPHAN_GHOST_HOST
    if not host_live and vm_in_vcenter:
        return STALE_INVENTORY
    if host_live and not vm_in_vcenter:
        return ORPHAN_LIVE_HOST
    return OK


def audit_segment_ports(
    nsx: NsxClient,
    segment: dict,
    vc: vCenter | None = None,
) -> list[dict]:
    """Classify every port on `segment`. Read-only and silent.

    Returns one record per port; `deletable` marks the ports that
    delete_orphan_ports() would remove and `delete_path` is the policy path
    it would DELETE.
    """
    seg_name = segment.get("display_name") or segment.get("id")
    seg_path = segment["path"]
    live_hosts = get_live_host_ids(nsx)
    ports = _results(nsx, f"/policy/api/v1{seg_path}/ports")

    records = []
    for port in ports:
        vif_id = (port.get("attachment") or {}).get("id")
        vifs = (
            _results(nsx, "/api/v1/fabric/vifs", lport_attachment_id=vif_id)
            if vif_id
            else []
        )
        rec = {
            "segment": seg_name,
            "port_id": port.get("id"),
            "port_name": port.get("display_name"),
            "vif_id": vif_id,
            "vm_name": None,
            "vm_external_id": None,
            "nsx_host_id": None,
            "nsx_host_live": None,
            "vm_in_vcenter": None,
            "delete_path": f"/policy/api/v1{port.get('path') or f'{seg_path}/ports/{port.get('id')}'}",
        }
        if vifs:
            # One VIF record per (VM, host); a stale inventory can hold several.
            vif = vifs[0]
            vms = _results(
                nsx,
                "/api/v1/fabric/virtual-machines",
                external_id=vif.get("owner_vm_id"),
            )
            vm = vms[0] if vms else {}
            rec["vm_name"] = vm.get("display_name")
            rec["vm_external_id"] = vm.get("external_id")
            rec["nsx_host_id"] = vm.get("host_id")
            rec["nsx_host_live"] = vm.get("host_id") in live_hosts
            if vc is not None and rec["vm_name"]:
                rec["vm_in_vcenter"] = vc.get_vm(rec["vm_name"]) is not None
        rec["verdict"] = classify(
            has_vif=bool(vifs),
            host_live=bool(rec["nsx_host_live"]),
            vm_in_vcenter=rec["vm_in_vcenter"],
        )
        rec["deletable"] = rec["verdict"] in DELETE_VERDICTS
        records.append(rec)
    return records


def audit_segment_ports_for_zpod(
    nsx: NsxClient, segment: dict, zpod: M.Zpod
) -> list[dict]:
    """audit_segment_ports with a vCenter session from the zPod's endpoint.

    If vCenter cannot be reached the classification still runs on NSX data
    alone, in which case no port is ever marked deletable.
    """
    try:
        with vCenter.auth_by_zpod_endpoint(zpod=zpod) as vc:
            return audit_segment_ports(nsx, segment, vc)
    except Exception as exc:  # the audit must never break the destroy flow
        print(
            f"{LOG_PREFIX} vCenter unavailable ({exc!r}); auditing with NSX data only"
        )
        return audit_segment_ports(nsx, segment, None)


def format_orphan_report(records: list[dict]) -> str:
    """Block listing the orphan ports (VM gone from vCenter) to delete."""
    deletable = [r for r in records if r["deletable"]]
    if not deletable:
        return f"{LOG_PREFIX} No orphan ports to delete."
    lines = [
        f"{LOG_PREFIX} VM & Orphan ports to delete "
        "(NSX inventory sync issue - Check with your NSX Admin)"
    ]
    lines += [f"- {r['vm_name']} ({r['port_id']})" for r in deletable]
    return "\n".join(lines)


def format_kept_report(records: list[dict]) -> str:
    """Block listing the ports still on the segment that will NOT be deleted."""
    kept = [r for r in records if not r["deletable"]]
    if not kept:
        return ""
    lines = [
        f"{LOG_PREFIX} Ports kept, not orphan "
        "(VM still exists in vCenter, or could not be resolved)"
    ]
    lines += [
        f"- {r['vm_name'] or r['port_name']} ({r['port_id']}) verdict={r['verdict']}"
        for r in kept
    ]
    return "\n".join(lines)


def delete_orphan_ports(nsx: NsxClient, records: list[dict]) -> list[dict]:
    """DELETE every deletable port in `records`; returns the ones removed."""
    deletable = [r for r in records if r["deletable"]]
    deleted = []
    for rec in deletable:
        print(f"DELETE: {rec['delete_path']}")
        response = nsx.delete(url=rec["delete_path"])
        if 200 <= response.status_code < 300 or response.status_code == 404:
            deleted.append(rec)
        else:
            print(
                f"{LOG_PREFIX} failed to delete {rec['port_id']} "
                f"(HTTP {response.status_code}): {response.text[:200]}"
            )
    print(f"{LOG_PREFIX} deleted {len(deleted)}/{len(deletable)} orphan port(s)")
    return deleted


def clean_orphan_ports_enabled() -> bool:
    value = DBUtils.get_setting_value(FF_CLEAN_ORPHAN_PORTS) or ""
    return value.strip().lower() == "true"


def evacuate_segment(nsx: NsxClient, segment: dict, zpod: M.Zpod) -> list[dict]:
    """Wait for the segment to drain, cleaning up orphan ports if it does not.

    Returns the list of ports deleted (empty on the normal path). Raises the
    original ValueError from wait_for_segment_to_be_evacuted when the segment
    still has ports and none of them qualifies for deletion, when the
    ff_nsx_clean_orphan_ports setting is not "true", or when the segment is
    still not empty after the cleanup.
    """
    try:
        wait_for_segment_to_be_evacuted(nsx, segment)
        return []
    except ValueError:
        records = audit_segment_ports_for_zpod(nsx, segment, zpod)
        enabled = clean_orphan_ports_enabled()
        print(format_orphan_report(records))
        if kept := format_kept_report(records):
            print(kept)
        print(
            f"{LOG_PREFIX} enabled={'true' if enabled else 'false'}"
            + (
                " -> deleting the orphan ports listed above"
                if enabled
                else " -> orphan ports reported only, nothing deleted "
                "(set the setting to 'true' to enable the cleanup)"
            )
        )
        if not enabled:
            raise
        deleted = delete_orphan_ports(nsx, records)
        if not deleted:
            raise
    # Ports were removed: give NSX a moment and confirm the segment is empty.
    wait_for_segment_to_be_evacuted(nsx, segment)
    return deleted
