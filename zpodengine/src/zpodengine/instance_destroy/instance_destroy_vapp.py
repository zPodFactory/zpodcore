from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib import database


@task(task_run_name="{instance_name}: delete vapp")
def instance_destroy_vapp(instance_id: int, instance_name: str):
    print("Delete Instance VAPP")
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        ep_compute = instance.endpoint.endpoints["compute"]
        v = vCenter(
            host=ep_compute["hostname"],
            user=ep_compute["username"],
            pwd=ep_compute["password"],
        )
        v.delete_vapp(f"zPod-{instance.name}")
