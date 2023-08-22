from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.network import get_instance_all_subnets, get_instance_primary_subnet
from zpodengine.lib import database


@task
def instance_deploy_prep(instance_id: int):
    # Add default network
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        instance.status = InstanceStatus.BUILDING

        if not instance.domain:
            domain = DBUtils.get_setting_value("zpodfactory_instances_domain")
            instance.domain = f"{instance.name}.{domain}"

        # Fetching main /24 network for Instance
        instance_primary_subnet = get_instance_primary_subnet(
            endpoint=instance.endpoint
        )

        # Fetching all 4 x /26 networks for Instance
        instance_subnets = get_instance_all_subnets(instance_primary_subnet)

        # Add networks to Instance
        for instance_subnet in instance_subnets:
            instance.networks.append(M.InstanceNetwork(cidr=instance_subnet))

        session.add(instance)
        session.commit()
