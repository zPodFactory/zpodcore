from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)
from zpodengine.instance_deploy.instance_deploy_1_prep import instance_deploy_prep
from zpodengine.instance_deploy.instance_deploy_2_dnsmasq import instance_deploy_dnsmasq
from zpodengine.instance_deploy.instance_deploy_3_networking import (
    instance_deploy_networking,
)
from zpodengine.instance_deploy.instance_deploy_4_vapp import instance_deploy_vapp
from zpodengine.instance_deploy.instance_deploy_5_get_profile import (
    instance_deploy_get_profile,
)
from zpodengine.instance_deploy.instance_deploy_6_finalize import (
    instance_deploy_finalize,
)
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup


def flow_failed(flow, flow_run, state):
    from prefect.logging.loggers import flow_run_logger

    logger = flow_run_logger(flow_run, flow)
    logger.info("FAILED")

    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, flow_run.parameters["instance_id"])
        instance.status = InstanceStatus.DEPLOY_FAILED
        session.add(instance)
        session.commit()


@flow(
    name="instance_deploy",
    flow_run_name="Deploy {instance_name}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_instance_deploy(
    instance_id: int,
    profile: str,
    instance_name: str,
    enet_name: str | None,
):
    options = task_options_setup(prefix=instance_name)

    # Prep
    prep = instance_deploy_prep.with_options(
        **options(name="prep"),
    ).submit(instance_id=instance_id)

    # Configure dnsmasq
    dnsmasq = instance_deploy_dnsmasq.with_options(
        **options(name="dnsmasq"),
    ).submit(
        instance_id=instance_id,
        wait_for=[prep],
    )

    # Configure Top Level Networking
    networking = instance_deploy_networking.with_options(
        **options(name="top level networking"),
    ).submit(
        instance_id=instance_id,
        enet_name=enet_name,
        wait_for=[dnsmasq],
    )

    # Create instance vapp
    vapp = instance_deploy_vapp.with_options(
        **options(name="vapp"),
    ).submit(
        instance_id=instance_id,
        wait_for=[networking],
    )

    # Get profile
    profile_obj = instance_deploy_get_profile.with_options(
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
                instance_component_add(
                    instance_id=instance_id,
                    instance_name=instance_name,
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
            last_component_item = instance_component_add(
                instance_id=instance_id,
                instance_name=instance_name,
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
    instance_deploy_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        instance_id=instance_id,
        wait_for=[last_component_item],
    )


if __name__ == "__main__":
    flow_instance_deploy(
        instance_id=21,
        profile="sddc",
        instance_name="kv8",
    )
