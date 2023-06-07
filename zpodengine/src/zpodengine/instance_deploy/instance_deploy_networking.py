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
def instance_deploy_networking(instance_id: int, enet_project_id: str | None = None):
    print("Configure top level networking")
    with InstanceDeployNetworking(
        instance_id=instance_id,
        enet_project_id=enet_project_id,
    ) as idn:
        idn()


class InstanceDeployNetworking:
    def __init__(
        self,
        instance_id: int,
        enet_project_id: str | None = None,
    ) -> None:
        self.session = database.get_session_raw()
        self.instance = self.session.get(M.Instance, instance_id)
        self.nsx = NsxClient(self.instance.endpoint)
        self.enet_project_id = enet_project_id

        inst_prefix = f"{settings.SITE_ID}-{self.instance.name}"
        project_prefix = enet_project_id[:-8] if enet_project_id else inst_prefix

        orgid = self.nsx.epnet.get("orgid", "default")
        self.tier0_path = f"/infra/tier-0s/{self.nsx.epnet['t0']}"
        self.project_id = enet_project_id or f"{inst_prefix}-project"
        self.project_path = f"/orgs/{orgid}/projects/{self.project_id}"
        self.tier1_id = f"{project_prefix}-tier1"
        self.mac_discovery_profile_id = f"{project_prefix}-mac-discovery-profile"
        self.locale_services_id = f"{project_prefix}-locale-services"
        self.dfw_allow_all_id = f"{project_prefix}-default-allow-all"
        self.segment_id = f"{inst_prefix}-segment"
        self.binding_map_id = f"{inst_prefix}-binding-map"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.close()

    def __call__(self):
        if not self.enet_project_id:
            self.project_create()
        self.t1_create()
        self.t1_attach_edge_cluster()
        self.segment_create()
        self.create_mac_discovery_profile()
        self.segment_set_mac_discovery_profile()
        self.add_dfw_allow_all_rule()
        # self.user_create()
        # self.attach_user_to_project()
        self.wait_for_segment_to_realize()

    def close(self):
        self.session.close()
        self.nsx.close()

    # @cached
    # def role_binding(self, username):
    #     return self.nsx.search_one(
    #         resource_type="RoleBinding",
    #         display_name=username,
    #     )

    def project_create(self):
        print(f"Create Project: {self.project_id}")
        self.nsx.patch(
            url=f"/policy/api/v1{self.project_path}",
            json=dict(
                id=self.project_id,
                tier_0s=[self.tier0_path],
                site_infos=[dict(edge_cluster_paths=[self.nsx.edge_cluster_path()])],
            ),
        )

    def t1_create(self) -> None:
        print(f"Create T1: {self.tier1_id}")
        self.nsx.patch(
            url=f"/policy/api/v1{self.project_path}/infra/tier-1s/{self.tier1_id}",
            json=dict(
                arp_limit=5000,
                id=self.tier1_id,
                ha_mode="ACTIVE_STANDBY",
                route_advertisement_types=[
                    "TIER1_CONNECTED",
                    "TIER1_IPSEC_LOCAL_ENDPOINT",
                ],
                tier0_path=self.tier0_path,
            ),
        )

    def t1_attach_edge_cluster(self) -> None:
        print(f"Attach Edge Cluster to T1: {self.tier1_id}")
        self.nsx.patch(
            url=(
                f"/policy/api/v1{self.project_path}/infra/tier-1s/{self.tier1_id}"
                f"/locale-services/{self.locale_services_id}"
            ),
            json=dict(
                edge_cluster_path=self.nsx.edge_cluster_path(),
            ),
        )

    def segment_create(self) -> None:
        print(f"Create Segment: {self.segment_id}")
        self.nsx.patch(
            url=f"/policy/api/v1{self.project_path}/infra/segments/{self.segment_id}",
            json=dict(
                id=self.segment_id,
                connectivity_path=(
                    f"{self.project_path}/infra/tier-1s/{self.tier1_id}"
                ),
                subnets=[
                    dict(gateway_address=MgmtIp.instance(self.instance, "gw").cidr)
                ],
                transport_zone_path=self.nsx.transport_zone_path(),
                vlan_ids=["0-4094"],
            ),
        )

    def create_mac_discovery_profile(self) -> None:
        print(f"Create MAC Discovery Profile: {self.mac_discovery_profile_id}")
        self.nsx.patch(
            url=(
                f"/policy/api/v1{self.project_path}"
                f"/infra/mac-discovery-profiles/{self.mac_discovery_profile_id}"
            ),
            json=dict(
                id=self.mac_discovery_profile_id,
                mac_learning_enabled=True,
            ),
        )

    def segment_set_mac_discovery_profile(self) -> None:
        print(
            f"Set Mac Discovery Profile on {self.segment_id} "
            f"to {self.mac_discovery_profile_id}"
        )
        self.nsx.patch(
            url=(
                f"/policy/api/v1{self.project_path}/infra/segments/{self.segment_id}"
                f"/segment-discovery-profile-binding-maps/{self.binding_map_id}"
            ),
            json=dict(
                mac_discovery_profile_path=(
                    f"{self.project_path}"
                    f"/infra/mac-discovery-profiles/{self.mac_discovery_profile_id}"
                )
            ),
        )

    def add_dfw_allow_all_rule(
        self,
        domain_id="default",
        security_policies_id="default-layer3-section",
    ) -> None:
        url = (
            f"/policy/api/v1{self.project_path}/infra/domains/{domain_id}"
            f"/security-policies/{security_policies_id}"
            f"/rules/{self.dfw_allow_all_id}"
        )
        if not self.nsx.get(url=url):
            self.nsx.patch(
                url=url,
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

    # def user_create(self, username):
    #     print(f"Create User: {username}")
    #     self.nsx.post(
    #         url="/api/v1/node/users?action=create_user",
    #         json=dict(
    #             full_name=username,
    #             username=username,
    #             password="PAssword1!PAssword1!",
    #         ),
    #     )

    # def attach_user_to_project(self, username):
    #     print(f"Attach User: {username} to Project: {self.project_name}")
    #     rb = self.role_binding(username)
    #     self.nsx.put(
    #         url=f"/api/v1/aaa/role-bindings/{rb['id']}",
    #         json=dict(
    #             name=username,
    #             type="local_user",
    #             identity_source_id=None,
    #             read_roles_for_paths=True,
    #             _revision=rb["_revision"],
    #             roles_for_paths=[
    #                 dict(
    #                     path=f"/orgs/default/projects/{self.project_name}",
    #                     roles=[
    #                         dict(
    #                             role="project_admin",
    #                             role_display_name="Project Admin",
    #                         )
    #                     ],
    #                 ),
    #             ],
    #         ),
    #     )

    def wait_for_segment_to_realize(self) -> None:
        print("Wait for segment to realize")
        start = datetime.now()
        while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_REALIZED:
            if not (
                results := self.nsx.get(
                    f"/policy/api/v1{self.project_path}"
                    "/infra/realized-state/realized-entities"
                    f"?intent_path={self.project_path}"
                    f"/infra/segments/{self.segment_id}"
                ).results()
            ):
                rls = next(
                    x for x in results if x["entity_type"] == "RealizedLogicalSwitch"
                )
                if rls["state"] == "REALIZED" and rls["runtime_status"] in (
                    "UP",
                    "SUCCESS",
                ):
                    print(f"Segment ({self.segment_id}) is ready for use")
                    break
                print(
                    f"Segment ({self.segment_id}) is not ready. "
                    f"State:{rls['state']}, "
                    f"Runtime Status:{rls['runtime_status']}"
                )
            else:
                print("Status not readable.  Trying again...")
            time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
        else:
            raise ValueError("Failed: Segment is not realized.")


if __name__ == "__main__":
    instance_deploy_networking.fn(5)
