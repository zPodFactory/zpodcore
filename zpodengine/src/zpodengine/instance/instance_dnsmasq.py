from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database


@task(task_run_name="{instance_name}: configure dnsmasq")
def instance_dnsmasq(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        print(f"Set DNSMASQ using the {instance.networks[0].cidr} network")
