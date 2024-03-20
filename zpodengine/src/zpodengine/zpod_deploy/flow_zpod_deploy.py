from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_component_add.zpod_component_add import (
    zpod_component_add,
)
from zpodengine.zpod_deploy.zpod_deploy_1_prep import zpod_deploy_prep
from zpodengine.zpod_deploy.zpod_deploy_2_dnsmasq import zpod_deploy_dnsmasq
from zpodengine.zpod_deploy.zpod_deploy_3_networking import (
    zpod_deploy_networking,
)
from zpodengine.zpod_deploy.zpod_deploy_4_vapp import zpod_deploy_vapp
from zpodengine.zpod_deploy.zpod_deploy_5_get_profile import (
    zpod_deploy_get_profile,
)
from zpodengine.zpod_deploy.zpod_deploy_6_finalize import (
    zpod_deploy_finalize,
)


def flow_failed(flow, flow_run, state):
    from prefect.logging.loggers import flow_run_logger

    logger = flow_run_logger(flow_run, flow)
    logger.info("FAILED")

    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, flow_run.parameters["zpod_id"])
        zpod.status = ZpodStatus.DEPLOY_FAILED
        session.add(zpod)
        session.commit()


@flow(
    name="zpod_deploy",
    flow_run_name="Deploy {zpod_name}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_deploy(
    zpod_id: int,
    profile: str,
    zpod_name: str,
    enet_name: str | None,
):
    options = task_options_setup(prefix=zpod_name)

    # Prep
    prep = zpod_deploy_prep.with_options(
        **options(name="prep"),
    ).submit(zpod_id=zpod_id)

    # Configure dnsmasq
    dnsmasq = zpod_deploy_dnsmasq.with_options(
        **options(name="dnsmasq"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[prep],
    )

    # Configure Top Level Networking
    networking = zpod_deploy_networking.with_options(
        **options(name="top level networking"),
    ).submit(
        zpod_id=zpod_id,
        enet_name=enet_name,
        wait_for=[dnsmasq],
    )

    # Create zPod vapp
    vapp = zpod_deploy_vapp.with_options(
        **options(name="vapp"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[networking],
    )

    # Get profile
    profile_obj = zpod_deploy_get_profile.with_options(
        **options(name="get_profile"),
    )(
        profile_name=profile,
        wait_for=[vapp],
    )

    # Deploy profile components
    last_component_item = None
    wait_for = [profile_obj]
    for profile_item in profile_obj:
        print(profile_item)
        if isinstance(profile_item, list):
            # Add in parallel
            last_component_item = [
                zpod_component_add(
                    zpod_id=zpod_id,
                    zpod_name=zpod_name,
                    component_uid=sub_profile_item.get("component_uid"),
                    host_id=sub_profile_item.get("host_id"),
                    hostname=sub_profile_item.get("hostname"),
                    vcpu=sub_profile_item.get("vcpu"),
                    vmem=sub_profile_item.get("vmem"),
                    vdisks=sub_profile_item.get("vdisks"),
                    wait_for=wait_for,
                )
                for sub_profile_item in profile_item
            ]
        else:
            # Add serial (wait for previous to finish)
            last_component_item = zpod_component_add(
                zpod_id=zpod_id,
                zpod_name=zpod_name,
                component_uid=profile_item.get("component_uid"),
                host_id=profile_item.get("host_id"),
                hostname=profile_item.get("hostname"),
                vcpu=profile_item.get("vcpu"),
                vmem=profile_item.get("vmem"),
                vdisks=profile_item.get("vdisks"),
                wait_for=wait_for,
            )
        wait_for = [last_component_item]

    # Finalize
    zpod_deploy_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[last_component_item],
    )


if __name__ == "__main__":
    flow_zpod_deploy(
        zpod_id=21,
        profile="sddc",
        zpod_name="kv8",
    )
