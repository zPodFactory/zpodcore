from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database

from .networking_deploy_nsxt import networking_deploy_nsxt
from .networking_deploy_nsxt_project import networking_deploy_nsxt_project


@task(tags=["atomic_operation"])
def zpod_deploy_networking(zpod_id: int, enet_name: str | None = None):
    with database.get_session_ctx() as session:
        zpod: M.Zpod = session.get(M.Zpod, zpod_id)
        driver = zpod.endpoint.endpoints["network"]["driver"]
        match driver:
            case "nsxt":
                return networking_deploy_nsxt(zpod, enet_name)
            case "nsxt_projects":
                return networking_deploy_nsxt_project(zpod, enet_name)
            case _:
                raise f"Unknown driver: {driver}"
