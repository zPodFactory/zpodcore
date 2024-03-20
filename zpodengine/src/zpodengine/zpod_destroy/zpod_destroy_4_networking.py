from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database

from .networking_destroy_nsxt import networking_destroy_nsxt
from .networking_destroy_nsxt_project import networking_destroy_nsxt_project


@task(tags=["atomic_operation"])
# This operation does not support concurrent calls.
# Adding tags["atomic_operation"] to task will disable concurrency
def zpod_destroy_networking(zpod_id: int):
    print("Destroy top level networking")

    with database.get_session_ctx() as session:
        zpod: M.Zpod = session.get(M.Zpod, zpod_id)
        driver = zpod.endpoint.endpoints["network"]["driver"]
        match driver:
            case "nsxt":
                return networking_destroy_nsxt(zpod)
            case "nsxt-projects":
                return networking_destroy_nsxt_project(zpod)
            case _:
                raise f"Unknown driver: {driver}"
