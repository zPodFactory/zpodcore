from zpodapi import settings
from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class EndpointENetService(ServiceBase):
    base_model: None

    def get_all(
        self,
        endpoint: M.Endpoint,
    ):
        with NsxClient(endpoint=endpoint) as nsx:
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
        with NsxClient(endpoint=endpoint) as nsx:
            projects = nsx.get(url="/policy/api/v1/orgs/default/projects").results()
            target_project_id = f"{settings.SITE_ID}-{name}-enet-project"
            return next(
                (build_enet_dict(x) for x in projects if x["id"] == target_project_id)
            )

    def create(
        self,
        *,
        endpoint: M.Endpoint,
        name: str,
    ):
        project_id = f"{settings.SITE_ID}-{name}-enet-project"
        with NsxClient(endpoint=endpoint) as nsx:
            nsx.patch(
                url=f"/policy/api/v1/orgs/default/projects/{project_id}",
                json=dict(
                    id=project_id,
                    tier_0s=[f"/infra/tier-0s/{nsx.epnet['t0']}"],
                    site_infos=[dict(edge_cluster_paths=[nsx.edge_cluster_path()])],
                ),
            )

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
            deployment_name="default",
            run_name=f"Destroy ENet.  Endpoint: {endpoint.id}, Project: {project_id}",
            project_id=project_id,
            endpoint_id=endpoint.id,
        )


def build_enet_dict(x):
    return dict(
        project_id=x["id"],
        name=x["id"].removeprefix(f"{settings.SITE_ID}-").removesuffix("-enet-project"),
    )
