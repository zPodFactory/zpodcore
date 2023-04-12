from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.vmware import vCenter
from zpodengine.lib import database


@task(task_run_name="{instance_name}: create vapp")
def instance_vapp(instance_id: int, instance_name: str):
    print("Create Instance VAPP")
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        hostname = instance.endpoint.endpoints["compute"]["hostname"]
        username = instance.endpoint.endpoints["compute"]["username"]
        password = instance.endpoint.endpoints["compute"]["password"]

        v = vCenter(hostname, username, password)
        v.create_vapp(f"zPod-{instance.name}", "Cluster", "zPods")
