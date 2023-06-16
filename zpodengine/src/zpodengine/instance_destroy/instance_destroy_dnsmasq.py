from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database, dnsmasq


@task
def instance_destroy_dnsmasq(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Destroy dnsmasq configuration
        dnsmasq.delete(instance_name=instance.name)
