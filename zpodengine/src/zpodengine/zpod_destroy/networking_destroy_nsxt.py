from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodengine import settings
from zpodengine.lib.network import fmt, wait_for_segment_to_be_evacuted


def networking_destroy_nsxt(zpod: M.Zpod):
    inst_prefix = f"{settings.SITE_ID}-{zpod.name}"
    t1_name = f"{inst_prefix}-tier1"
    t1_path = f"/infra/tier-1s/{t1_name}"
    print(f"Destroy {t1_name}")

    with NsxClient.auth_by_zpod(zpod) as nsx:
        # Destroy Connected Items (Segments)
        for connected in nsx.search(connectivity_path=fmt(t1_path)):
            if connected["resource_type"] == "Segment":
                wait_for_segment_to_be_evacuted(nsx, connected)

                # Destroy Connected Item Children (Segment BindingMaps)
                for connected_child in nsx.search(parent_path=fmt(connected["path"])):
                    delete(nsx, connected_child["path"])
            delete(nsx, connected["path"])

        # Destroy Children (LocaleServices)
        for child in nsx.search(parent_path=fmt(t1_path)):
            if child["resource_type"] not in ("SecurityFeatures", "PolicyNat"):
                delete(nsx, child["path"])

        # Destroy T1
        delete(nsx, t1_path)

        # Destroy MacDiscoveryProfile Binding Map
        delete(
            nsx,
            f"/infra/mac-discovery-profiles/{inst_prefix}-mac-discovery-profile",
        )

        # Destroy SegmentSecurityProfile Binding Map
        delete(
            nsx,
            f"/infra/segment-security-profiles/{inst_prefix}-segment-security-profile",
        )


def delete(nsx, path):
    print(f"DELETE: {path}")
    nsx.delete(url=f"/policy/api/v1{path}")
