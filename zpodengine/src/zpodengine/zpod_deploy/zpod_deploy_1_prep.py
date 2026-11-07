from ipaddress import IPv4Network

from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ZpodNetworkKind, ZpodStatus
from zpodcommon.lib.dbutils import DBUtils
from zpodengine.lib import database
from zpodengine.lib.network import (
    ZPOD_PUBLIC_NETWORK_PREFIXLEN,
    get_zpod_all_subnets,
    get_zpod_primary_subnet,
)
from zpodengine.lib.zpod_status import set_zpod_status


@task(tags=["atomic_operation"])
def zpod_deploy_prep(zpod_id: int):
    # Add default network
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        set_zpod_status(zpod, ZpodStatus.BUILDING)

        if not zpod.domain:
            domain = DBUtils.get_setting_value("zpodfactory_default_domain")
            zpod.domain = f"{zpod.name}.{domain}"

        # Idempotent: a re-run of this flow run (Retry in Prefect, a crashed run
        # run again) keeps the /24 the first run allocated. Allocating again gave
        # the zPod a second /24 and 4 more rows, which the (zpod_id, vlan_id)
        # unique constraint of 0.9.0 now refuses.
        deploy_networks = [
            n for n in zpod.networks if n.kind == ZpodNetworkKind.ZPOD.value
        ]
        if deploy_networks:
            print(
                f"zPod {zpod.name} already has its networks "
                f"({', '.join(str(n.cidr) for n in deploy_networks)}): reusing them"
            )
            session.add(zpod)
            session.commit()
            return

        # The /24s of every other zPod not yet DELETED (destroying, kept as
        # DEPLOY_FAILED, ...). This task holds the atomic_operation lock and
        # commits its own rows before releasing it, so the next prep sees them.
        taken = [
            IPv4Network(cidr)
            for cidr in session.exec(
                select(M.ZpodNetwork.cidr)
                .join(M.Zpod)
                .where(
                    M.Zpod.id != zpod.id,
                    M.Zpod.status != ZpodStatus.DELETED,
                    M.ZpodNetwork.kind == ZpodNetworkKind.ZPOD.value,
                )
            )
        ]

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
                        endpoint=zpod.endpoint, taken=taken
                    )
            except ValueError as e:
                print(
                    f"Invalid subnet format in feature flag ff_zpod_{zpod.name}_subnet: {e}"
                )
                print("Falling back to default subnet allocation")
                zpod_primary_subnet = get_zpod_primary_subnet(
                    endpoint=zpod.endpoint, taken=taken
                )
        else:
            # Fetching main /24 network for zPod
            zpod_primary_subnet = get_zpod_primary_subnet(
                endpoint=zpod.endpoint, taken=taken
            )

        # Fetching all 4 x /26 networks for zPod
        zpod_subnets = get_zpod_all_subnets(zpod_primary_subnet)

        # Add networks to zPod
        for zpod_subnet in zpod_subnets:
            zpod.networks.append(M.ZpodNetwork.deploy_row(zpod_subnet))

        session.add(zpod)
        session.commit()
