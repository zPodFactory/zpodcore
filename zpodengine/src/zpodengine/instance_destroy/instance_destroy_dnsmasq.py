from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import delete_dnsmasq_config
from zpodengine.lib import database


@task(task_run_name="{instance_name}: remove dnsmasq")
def instance_destroy_dnsmasq(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Destroy dnsmasq configuration
        delete_dnsmasq_config(instance_name=instance.name)
