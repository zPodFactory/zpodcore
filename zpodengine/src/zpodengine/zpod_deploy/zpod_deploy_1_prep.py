from ipaddress import IPv4Network

from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodengine.lib import database
from zpodengine.lib.network import (
    ZPOD_PUBLIC_NETWORK_PREFIXLEN,
    get_zpod_all_subnets,
    get_zpod_primary_subnet,
)


@task(tags=["atomic_operation"])
def zpod_deploy_prep(zpod_id: int):
    # Add default network
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.BUILDING

        if not zpod.domain:
            domain = DBUtils.get_setting_value("zpodfactory_default_domain")
            zpod.domain = f"{zpod.name}.{domain}"

        # Check for custom subnet feature flag
        custom_subnet = DBUtils.get_setting_value(f"ff_zpod_{zpod.name}_subnet")
        if custom_subnet:
            try:
                zpod_primary_subnet = IPv4Network(custom_subnet)
                if zpod_primary_subnet.prefixlen != ZPOD_PUBLIC_NETWORK_PREFIXLEN:
                    print(
                        f"Invalid subnet prefix length in feature flag ff_zpod_{zpod.name}_subnet. "
                        f"Expected /{ZPOD_PUBLIC_NETWORK_PREFIXLEN}, got /{zpod_primary_subnet.prefixlen}"
                    )
                    print("Falling back to default subnet allocation")
                    zpod_primary_subnet = get_zpod_primary_subnet(
                        endpoint=zpod.endpoint
                    )
            except ValueError as e:
                print(
                    f"Invalid subnet format in feature flag ff_zpod_{zpod.name}_subnet: {e}"
                )
                print("Falling back to default subnet allocation")
                zpod_primary_subnet = get_zpod_primary_subnet(endpoint=zpod.endpoint)
        else:
            # Fetching main /24 network for zPod
            zpod_primary_subnet = get_zpod_primary_subnet(endpoint=zpod.endpoint)

        # Fetching all 4 x /26 networks for zPod
        zpod_subnets = get_zpod_all_subnets(zpod_primary_subnet)

        # Add networks to zPod
        for zpod_subnet in zpod_subnets:
            zpod.networks.append(M.ZpodNetwork(cidr=zpod_subnet))

        session.add(zpod)
        session.commit()
