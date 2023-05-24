from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.network import create_dnsmasq_config, MgmtIp
from zpodengine.lib import database


@task
def instance_deploy_dnsmasq(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Fetch associate zbox IP from subnet
        dns_ip = MgmtIp.instance(instance, "zbox").ip

        # Create dnsmasq configuration
        create_dnsmasq_config(instance.name, instance.domain, dns_ip)
