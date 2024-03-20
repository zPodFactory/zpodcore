from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database
from zpodengine.lib.dbutils import DBUtils
from zpodengine.lib.network import get_zpod_all_subnets, get_zpod_primary_subnet


@task
def zpod_deploy_prep(zpod_id: int):
    # Add default network
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.BUILDING

        if not zpod.domain:
            domain = DBUtils.get_setting_value("zpodfactory_default_domain")
            zpod.domain = f"{zpod.name}.{domain}"

        # Fetching main /24 network for zPod
        zpod_primary_subnet = get_zpod_primary_subnet(endpoint=zpod.endpoint)

        # Fetching all 4 x /26 networks for zPod
        zpod_subnets = get_zpod_all_subnets(zpod_primary_subnet)

        # Add networks to zPod
        for zpod_subnet in zpod_subnets:
            zpod.networks.append(M.ZpodNetwork(cidr=zpod_subnet))

        session.add(zpod)
        session.commit()
