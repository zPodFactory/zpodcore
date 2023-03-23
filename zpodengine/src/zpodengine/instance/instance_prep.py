from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database


def get_available_network():
    return "192.168.0.0/24"


@task(task_run_name="{instance_name}: prep")
def instance_prep(instance_id: int, instance_name: str):
    # Add default network
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        instance.status = "ACTIVE"
        instance.networks.append(M.InstanceNetwork(cidr=get_available_network()))
        session.add(instance)
        session.commit()
