import time
from datetime import datetime

from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import get_mgmt_cidr
from zpodcommon.lib.nsx import NsxClient
from zpodengine.lib import database

SEGMENT_MAX_WAIT_FOR_REALIZED = 120
SEGMENT_WAIT_BETWEEN_TRIES = 5


@task(task_run_name="{instance_name}: configure top level networking")
def instance_deploy_networking(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        print(
            f"Configure top level networking with {instance.networks[0].cidr} network"
        )

        with NsxClient.auth_by_instance(instance) as nsx:
            tln = TopLevelNetworking(nsx=nsx, instance=instance)
            tln.t1_create()
            tln.t1_attach_edge_cluster()
            tln.segment_create()
            tln.segment_set_mac_discovery_profile()
            tln.wait_for_segment_to_realize()


class TopLevelNetworking:
    def __init__(self, nsx: NsxClient, instance: M.Instance) -> None:
        self.nsx = nsx
        self.instance = instance
        self.epnet = instance.endpoint.endpoints["network"]

        self.instance_name = instance.name
        self.t1_name = f"T1-zPod-{self.instance_name}"
        self.segment_name = f"Segment-zPod-{self.instance_name}"

    def t1_create(self) -> None:
        print(f"Create T1: {self.t1_name}")
        t0_name = self.epnet["t0"]
        self.nsx.patch(
            url=f"/v1/infra/tier-1s/{self.t1_name}",
            json=dict(
                arp_limit=5000,
                id=self.t1_name,
                ha_mode="ACTIVE_STANDBY",
                route_advertisement_types=[
                    "TIER1_CONNECTED",
                    "TIER1_IPSEC_LOCAL_ENDPOINT",
                ],
                tier0_path=f"/infra/tier-0s/{t0_name}",
            ),
        )

    def t1_attach_edge_cluster(self) -> None:
        edge_cluster_name = self.epnet["edgecluster"]
        print(f"Attach Edge Cluster: {edge_cluster_name} to T1: {self.t1_name}")
        edge_cluster = self.nsx.search_one(
            resource_type="PolicyEdgeCluster",
            display_name=edge_cluster_name,
        )
        self.nsx.patch(
            url=(
                f"/v1/infra/tier-1s/{self.t1_name}"
                f"/locale-services/LocaleService-{self.instance_name}"
            ),
            json=dict(edge_cluster_path=edge_cluster["path"]),
        )

    def segment_create(self) -> None:
        print(f"Create Segment: {self.segment_name}")
        transport_zone = self.nsx.search_one(
            resource_type="PolicyTransportZone",
            display_name=self.epnet["transportzone"],
        )
        self.nsx.patch(
            url=f"/v1/infra/segments/{self.segment_name}",
            json=dict(
                id=self.segment_name,
                connectivity_path=f"/infra/tier-1s/{self.t1_name}",
                subnets=[dict(gateway_address=get_mgmt_cidr(self.instance, "gw"))],
                transport_zone_path=transport_zone["path"],
                vlan_ids=["0-4094"],
            ),
        )

    def segment_set_mac_discovery_profile(self) -> None:
        mac_discovery_profile = self.epnet["macdiscoveryprofile"]
        print(
            f"Set Mac Discovery Profile on {self.segment_name} "
            f"to {mac_discovery_profile}"
        )
        self.nsx.patch(
            url=(
                f"/v1/infra/segments/{self.segment_name}"
                "/segment-discovery-profile-binding-maps"
                f"/BindingMap-{self.instance_name}"
            ),
            json=dict(
                mac_discovery_profile_path=(
                    f"/infra/mac-discovery-profiles/{mac_discovery_profile}"
                )
            ),
        )

    def wait_for_segment_to_realize(self) -> None:
        print("Wait for segment to realize")
        start = datetime.now()
        while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_REALIZED:
            real = self.nsx.get(
                "/v1/infra/realized-state/realized-entities"
                f"?intent_path=/infra/segments/{self.segment_name}"
            ).safejson()
            if real.get("results"):
                rls = next(
                    x
                    for x in real["results"]
                    if x["entity_type"] == "RealizedLogicalSwitch"
                )
                if rls["state"] == "REALIZED" and rls["runtime_status"] == "SUCCESS":
                    print(f"Segment ({self.segment_name}) is ready for use")
                    break
                print(
                    f"Segment ({self.segment_name}) is not ready. "
                    f"State:{rls['state']}, "
                    f"Runtime Status:{rls['runtime_status']}"
                )
            else:
                print("Status not readable.  Trying again...")
            time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
        else:
            raise ValueError("Failed: Segment is not realized.")


if __name__ == "__main__":
    instance_deploy_networking.fn(22, "test")
