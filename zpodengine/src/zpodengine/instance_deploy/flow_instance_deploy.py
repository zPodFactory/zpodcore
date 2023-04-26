import importlib

from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
from zpodengine.instance_deploy.instance_deploy_dnsmasq import instance_deploy_dnsmasq
from zpodengine.instance_deploy.instance_deploy_finalize import instance_deploy_finalize
from zpodengine.instance_deploy.instance_deploy_networking import (
    instance_deploy_networking,
)
from zpodengine.instance_deploy.instance_deploy_prep import instance_deploy_prep
from zpodengine.instance_deploy.instance_deploy_vapp import instance_deploy_vapp
from zpodengine.lib import database


def flow_failed(flow, flow_run, state):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, flow_run.parameters["instance_id"])
        instance.status = InstanceStatus.FAILED
        session.add(instance)
        session.commit()


@flow(
    name="instance_deploy",
    flow_run_name="deploy_{instance_name}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_instance_deploy(
    instance_id: int,
    profile: str,
    instance_name: str,
):
    # Prep
    prep = instance_deploy_prep.submit(
        instance_id=instance_id,
        instance_name=instance_name,
    )

    # Configure dnsmasq
    dnsmasq = instance_deploy_dnsmasq.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[prep],
    )

    # Configure Top Level Networking
    networking = instance_deploy_networking.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[dnsmasq],
    )

    # Create instance vapp
    vapp = instance_deploy_vapp.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[networking],
    )

    # # Deploy profile components
    mod = importlib.import_module(f"zpodengine.instance_profiles.{profile}")
    last_component_task = mod.instance_profile_flow(
        instance_id=instance_id,
        wait_for=[vapp],
    )

    instance_deploy_finalize.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[last_component_task],
    )


if __name__ == "__main__":
    flow_instance_deploy(
        instance_id=21,
        profile="sddc",
        instance_name="kv8",
    )
