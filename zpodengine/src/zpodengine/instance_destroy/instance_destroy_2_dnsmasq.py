from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database, dnsmasq


@task
def instance_destroy_dnsmasq(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        cidr = instance.networks[0].cidr
        subnet = ".".join(cidr.split(".")[:3])
        # Destroy dnsmasq configuration
        dnsmasq.delete(subnet=subnet)
