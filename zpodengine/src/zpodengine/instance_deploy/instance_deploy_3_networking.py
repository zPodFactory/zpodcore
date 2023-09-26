import time
from datetime import datetime

from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import MgmtIp
from zpodcommon.lib.nsx import NsxClient
from zpodengine import settings
from zpodengine.lib import database

SEGMENT_MAX_WAIT_FOR_REALIZED = 120
SEGMENT_WAIT_BETWEEN_TRIES = 5


@task
def instance_deploy_networking(instance_id: int, enet_name: str | None = None):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        with NsxClient(instance.endpoint) as nsx:
            inst_prefix = f"{settings.SITE_ID}-{instance.name}"
            project_prefix = enet_name[:-8] if enet_name else inst_prefix

            orgid = nsx.epnet.get("orgid", "default")
            tier0_path = f"/infra/tier-0s/{nsx.epnet['t0']}"
            project_id = enet_name or f"{inst_prefix}-project"
            project_path = f"/orgs/{orgid}/projects/{project_id}"
            policy_project_path = f"/policy/api/v1{project_path}"

            # Create Project
            if not enet_name:
                print(f"Create Project: {project_id}")
                nsx.patch(
                    url=policy_project_path,
                    json=dict(
                        id=project_id,
                        tier_0s=[tier0_path],
                        site_infos=[dict(edge_cluster_paths=[nsx.edge_cluster_path()])],
                    ),
                )

            # Create T1
            tier1_id = f"{project_prefix}-tier1"
            print(f"Create T1: {tier1_id}")
            nsx.patch(
                url=f"{policy_project_path}/infra/tier-1s/{tier1_id}",
                json=dict(
                    arp_limit=5000,
                    id=tier1_id,
                    ha_mode="ACTIVE_STANDBY",
                    route_advertisement_types=[
                        "TIER1_CONNECTED",
                        "TIER1_IPSEC_LOCAL_ENDPOINT",
                        "TIER1_STATIC_ROUTES",
                    ],
                    tier0_path=tier0_path,
                ),
            )

            # Attach Edge Cluster to T1
            print(f"Attach Edge Cluster to T1: {tier1_id}")
            nsx.patch(
                url=(
                    f"{policy_project_path}/infra/tier-1s/{tier1_id}"
                    f"/locale-services/{project_prefix}-locale-services"
                ),
                json=dict(
                    edge_cluster_path=nsx.edge_cluster_path(),
                ),
            )

            # Create Segment
            segment_id = f"{inst_prefix}-segment"
            print(f"Create Segment: {segment_id}")
            nsx.patch(
                url=f"{policy_project_path}/infra/segments/{segment_id}",
                json=dict(
                    id=segment_id,
                    connectivity_path=(f"{project_path}/infra/tier-1s/{tier1_id}"),
                    subnets=[
                        dict(gateway_address=MgmtIp.instance(instance, "gw").cidr)
                    ],
                    transport_zone_path=nsx.transport_zone_path(),
                    vlan_ids=["0-4094"],
                ),
            )

            # Create MAC Discovery Profile
            mac_discovery_profile_id = f"{project_prefix}-mac-discovery-profile"
            print(f"Create MAC Discovery Profile: {mac_discovery_profile_id}")
            nsx.patch(
                url=(
                    f"{policy_project_path}/infra"
                    f"/mac-discovery-profiles/{mac_discovery_profile_id}"
                ),
                json=dict(
                    id=mac_discovery_profile_id,
                    mac_learning_enabled=True,
                ),
            )

            # Attach Mac Discovery Profile to segment
            print(
                f"Attach Mac Discovery Profile on {segment_id} "
                f"to {mac_discovery_profile_id}"
            )
            nsx.patch(
                url=(
                    f"{policy_project_path}/infra/segments/{segment_id}"
                    f"/segment-discovery-profile-binding-maps/{inst_prefix}-binding-map"
                ),
                json=dict(
                    mac_discovery_profile_path=(
                        f"{project_path}"
                        f"/infra/mac-discovery-profiles/{mac_discovery_profile_id}"
                    )
                ),
            )

            # Add DFW allow all rule
            dfw_allow_all_url = (
                f"{policy_project_path}/infra/domains/default"
                f"/security-policies/default-layer3-section"
                f"/rules/{project_prefix}-default-allow-all"
            )
            if not nsx.get(url=dfw_allow_all_url).safejson():
                nsx.patch(
                    url=dfw_allow_all_url,
                    json=dict(
                        description="zPod Default Allow All",
                        display_name="zPod Allow All",
                        sequence_number=1,
                        source_groups=["ANY"],
                        logged=False,
                        destination_groups=["ANY"],
                        scope=["ANY"],
                        action="ALLOW",
                        services=["ANY"],
                    ),
                )

            # Add Default Static Routes
            for network in instance.networks[1:]:
                id_host = network.cidr.split("/")[0].split(".")[3]
                nsx.patch(
                    url=(
                        f"{policy_project_path}/infra/tier-1s/{tier1_id}"
                        f"/static-routes/{instance.name}-vlan{id_host}"
                    ),
                    json=dict(
                        network=network.cidr,
                        next_hops=[
                            dict(
                                ip_address=MgmtIp.instance(instance, "zbox").ip,
                                admin_distance=1,
                            ),
                        ],
                    ),
                )

            # Wait for segment to realize
            print("Wait for segment to realize")
            start = datetime.now()
            while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_REALIZED:
                if results := nsx.get(
                    f"{policy_project_path}"
                    "/infra/realized-state/realized-entities"
                    f"?intent_path={project_path}"
                    f"/infra/segments/{segment_id}"
                ).results():
                    rls = next(
                        x
                        for x in results
                        if x["entity_type"] == "RealizedLogicalSwitch"
                    )
                    if (
                        rls.get("state") == "REALIZED"
                        and rls.get("runtime_status") == "SUCCESS"
                        and rls.get("publish_status") == "SUCCESS"
                        and rls.get("operational_status") == "STATUS_GREEN"
                    ):
                        print(f"Segment ({segment_id}) is ready for use")
                        break
                    print(
                        f"Segment ({segment_id}) is not ready. "
                        f"State:{rls.get('state', 'N/a')}, "
                        f"Runtime Status:{rls.get('runtime_status', 'N/a')}, "
                        f"Publish Status:{rls.get('publish_status', 'N/a')}, "
                        f"Operational Status:{rls.get('operational_status', 'N/a')}"
                    )
                else:
                    print("Status not readable.  Trying again...")
                time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
            else:
                raise ValueError("Failed: Segment is not realized.")
