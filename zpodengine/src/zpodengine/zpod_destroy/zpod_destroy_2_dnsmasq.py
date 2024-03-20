from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database, dnsmasq


@task
def zpod_destroy_dnsmasq(zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        if zpod.networks:
            cidr = zpod.networks[0].cidr
            subnet = ".".join(cidr.split(".")[:3])
            # Destroy dnsmasq configuration
            dnsmasq.delete(subnet=subnet)
