from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database


@task(task_run_name="{instance_name}: configure top level networking")
def instance_networking(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        print(
            f"Configure top level networking with {instance.networks[0].cidr} network"
        )
