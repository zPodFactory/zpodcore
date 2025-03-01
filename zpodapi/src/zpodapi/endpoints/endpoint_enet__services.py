from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from zpodapi import settings
from zpodapi.lib.service_base import ServiceBase


class EndpointENetService(ServiceBase):
    base_model: None

    def get_all(
        self,
        endpoint: M.Endpoint,
    ):
        with NsxClient.auth_by_endpoint(endpoint=endpoint) as nsx:
            projects = nsx.get(url="/policy/api/v1/orgs/default/projects").results()
            return [
                build_enet_dict(x)
                for x in projects
                if x["id"].endswith("-enet-project")
            ]

    def get(
        self,
        endpoint: M.Endpoint,
        name: str,
    ):
        with NsxClient.auth_by_endpoint(endpoint=endpoint) as nsx:
            projects = nsx.get(url="/policy/api/v1/orgs/default/projects").results()
            target_project_id = f"{settings.SITE_ID}-{name}-enet-project"
            return next(
                build_enet_dict(x) for x in projects if x["id"] == target_project_id
            )

    def create(
        self,
        *,
        endpoint: M.Endpoint,
        name: str,
    ):
        project_id = f"{settings.SITE_ID}-{name}-enet-project"
        epnet = endpoint.endpoints["network"]
        with NsxClient.auth_by_endpoint(endpoint=endpoint) as nsx:
            nsx.patch(
                url=f"/policy/api/v1/orgs/default/projects/{project_id}",
                json={
                    "id": project_id,
                    "tier_0s": [f"/infra/tier-0s/{epnet['t0']}"],
                    "site_infos": [
                        {
                            "edge_cluster_paths": [
                                nsx.edge_cluster_path(epnet["edgecluster"])
                            ]
                        }
                    ],
                },
            )
            # PS: This operation does not support concurrent calls.
            # Task in the engine are set with tags["atomic_operation"] to avoid this.

    def delete(
        self,
        *,
        endpoint: M.Endpoint,
        name: str,
    ):
        project_id = f"{settings.SITE_ID}-{name}-enet-project"
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="nsx_project_destroy",
            deployment_name="nsx_project_destroy",
            run_name=f"Destroy ENet.  Endpoint: {endpoint.id}, Project: {project_id}",
            project_id=project_id,
            endpoint_id=endpoint.id,
        )


def build_enet_dict(x):
    return {
        "project_id": x["id"],
        "name": x["id"]
        .removeprefix(f"{settings.SITE_ID}-")
        .removesuffix("-enet-project"),
    }
