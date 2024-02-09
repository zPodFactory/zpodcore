from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodengine import settings
from zpodengine.lib.network import MgmtIp, wait_for_segment_to_realize


#######################################################################################
def networking_deploy_nsxt_project(instance: M.Instance, enet_name: str | None = None):
    with NsxClient(instance.endpoint) as nsx:
        inst_prefix = f"{settings.SITE_ID}-{instance.name}"
        project_prefix = enet_name[:-8] if enet_name else inst_prefix

        orgid = nsx.epnet.get("orgid", "default")
        tier0_path = f"/infra/tier-0s/{nsx.epnet['t0']}"
        project_id = enet_name or f"{inst_prefix}-project"
        project_path = f"/orgs/{orgid}/projects/{project_id}"
        base_path = f"/policy/api/v1{project_path}"

        if not enet_name:
            print(f"Create Project: {project_id}")

            # Create Project
            # This operation does not support concurrent calls.
            # Adding tags["atomic_operation"] to task will disable concurrency
            nsx.patch(
                url=base_path,
                json={
                    "id": project_id,
                    "tier_0s": [tier0_path],
                    "site_infos": [{"edge_cluster_paths": [nsx.edge_cluster_path()]}],
                },
            )

        # Create T1
        tier1_id = f"{project_prefix}-tier1"
        print(f"Create T1: {tier1_id}")
        nsx.patch(
            url=f"{base_path}/infra/tier-1s/{tier1_id}",
            json={
                "arp_limit": 5000,
                "id": tier1_id,
                "ha_mode": "ACTIVE_STANDBY",
                "route_advertisement_types": [
                    "TIER1_CONNECTED",
                    "TIER1_IPSEC_LOCAL_ENDPOINT",
                    "TIER1_STATIC_ROUTES",
                ],
                "tier0_path": tier0_path,
            },
        )

        # Attach Edge Cluster to T1
        print(f"Attach Edge Cluster to T1: {tier1_id}")
        nsx.patch(
            url=(
                f"{base_path}/infra/tier-1s/{tier1_id}"
                f"/locale-services/{project_prefix}-locale-services"
            ),
            json={
                "edge_cluster_path": nsx.edge_cluster_path(),
            },
        )

        # Create Segment
        segment_id = f"{inst_prefix}-segment"
        print(f"Create Segment: {segment_id}")
        nsx.patch(
            url=f"{base_path}/infra/segments/{segment_id}",
            json={
                "id": segment_id,
                "connectivity_path": (f"{project_path}/infra/tier-1s/{tier1_id}"),
                "subnets": [{"gateway_address": MgmtIp.instance(instance, "gw").cidr}],
                "transport_zone_path": nsx.transport_zone_path(),
                "vlan_ids": ["0-4094"],
            },
        )

        # Create MAC Discovery Profile
        mac_discovery_profile_id = f"{project_prefix}-mac-discovery-profile"
        print(f"Create MAC Discovery Profile: {mac_discovery_profile_id}")
        nsx.patch(
            url=f"{base_path}/infra/mac-discovery-profiles/{mac_discovery_profile_id}",
            json={
                "id": mac_discovery_profile_id,
                "mac_learning_enabled": True,
            },
        )

        # Attach Mac Discovery Profile to segment
        print(
            f"Attach Mac Discovery Profile on {segment_id} "
            f"to {mac_discovery_profile_id}"
        )
        nsx.patch(
            url=(
                f"{base_path}/infra/segments/{segment_id}"
                "/segment-discovery-profile-binding-maps"
                f"/{inst_prefix}-mac-discovery-binding-map"
            ),
            json={
                "mac_discovery_profile_path": (
                    f"{project_path}"
                    f"/infra/mac-discovery-profiles/{mac_discovery_profile_id}"
                )
            },
        )

        # Create Segment Security Profile
        # - Allow DHCP Server on Segment such as zbox/vyos
        segment_security_profile_id = f"{project_prefix}-segment-security-profile"
        print(f"Create Segment Security Profile: {segment_security_profile_id}")
        nsx.patch(
            url=(
                f"{base_path}/infra"
                f"/segment-security-profiles/{segment_security_profile_id}"
            ),
            json={
                "id": segment_security_profile_id,
                "dhcp_server_block_enabled": False,
            },
        )

        # Attach Segment Security Profile to segment
        print(
            f"Attach Segment Security Profile on {segment_id} "
            f"to {segment_security_profile_id}"
        )
        nsx.patch(
            url=(
                f"{base_path}/infra/segments/{segment_id}"
                "/segment-security-profile-binding-maps"
                f"/{inst_prefix}-security-profile-binding-map"
            ),
            json={
                "segment_security_profile_path": (
                    f"{project_path}/infra"
                    f"/segment-security-profiles/{segment_security_profile_id}"
                )
            },
        )

        # Add DFW allow all rule
        dfw_allow_all_url = (
            f"{base_path}/infra/domains/default"
            "/security-policies/default-layer3-section"
            f"/rules/{project_prefix}-default-allow-all"
        )
        if not nsx.get(url=dfw_allow_all_url).safejson():
            nsx.patch(
                url=dfw_allow_all_url,
                json={
                    "description": "zPod Default Allow All",
                    "display_name": "zPod Allow All",
                    "sequence_number": 1,
                    "source_groups": ["ANY"],
                    "logged": False,
                    "destination_groups": ["ANY"],
                    "scope": ["ANY"],
                    "action": "ALLOW",
                    "services": ["ANY"],
                },
            )

        # Add Default Static Routes
        for network in instance.networks[1:]:
            id_host = network.cidr.split("/")[0].split(".")[3]
            nsx.patch(
                url=(
                    f"{base_path}/infra/tier-1s/{tier1_id}"
                    f"/static-routes/{instance.name}-vlan{id_host}"
                ),
                json={
                    "network": network.cidr,
                    "next_hops": [
                        {
                            "ip_address": MgmtIp.instance(instance, "zbox").ip,
                            "admin_distance": 1,
                        },
                    ],
                },
            )

        wait_for_segment_to_realize(
            nsx=nsx,
            path=(
                f"{base_path}/infra/realized-state/realized-entities"
                f"?intent_path={project_path}/infra/segments/{segment_id}"
            ),
            segment_id=segment_id,
        )
