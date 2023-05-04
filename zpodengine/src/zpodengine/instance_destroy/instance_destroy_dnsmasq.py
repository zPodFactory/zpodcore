from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import delete_dnsmasq_config
from zpodengine.lib import database


@task
def instance_destroy_dnsmasq(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Destroy dnsmasq configuration
        delete_dnsmasq_config(instance_name=instance.name)
