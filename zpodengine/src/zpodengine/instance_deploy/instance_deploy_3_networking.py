from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database

from .networking_deploy_nsxt import networking_deploy_nsxt
from .networking_deploy_nsxt_project import networking_deploy_nsxt_project


@task(tags=["atomic_operation"])
def instance_deploy_networking(instance_id: int, enet_name: str | None = None):
    with database.get_session_ctx() as session:
        instance: M.Instance = session.get(M.Instance, instance_id)
        driver = instance.endpoint.endpoints["network"]["driver"]
        match driver:
            case "nsxt":
                return networking_deploy_nsxt(instance, enet_name)
            case "nsxt-projects":
                return networking_deploy_nsxt_project(instance, enet_name)
            case _:
                raise f"Unknown driver: {driver}"
