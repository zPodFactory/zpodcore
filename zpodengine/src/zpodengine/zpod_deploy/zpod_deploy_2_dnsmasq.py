import time

from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database, dnsmasq
from zpodengine.lib.network import MgmtIp


@task
def zpod_deploy_dnsmasq(zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)

        # Fetch associate zbox IP from subnet
        dns_ip = MgmtIp.zpod(zpod, "zbox").ip

        # Create dnsmasq configuration
        dnsmasq.add(zpod.domain, dns_ip)

        # TODO: Add better code here
        time.sleep(5)
