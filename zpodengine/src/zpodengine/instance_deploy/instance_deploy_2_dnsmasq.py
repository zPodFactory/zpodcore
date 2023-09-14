import time

from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import MgmtIp
from zpodengine.lib import database, dnsmasq


@task
def instance_deploy_dnsmasq(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Fetch associate zbox IP from subnet
        dns_ip = MgmtIp.instance(instance, "zbox").ip

        # Create dnsmasq configuration
        dnsmasq.add(instance.domain, dns_ip)

        # TODO: Add better code here
        time.sleep(5)