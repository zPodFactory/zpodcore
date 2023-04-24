import importlib

from prefect import flow

from zpodengine.instance_deploy.instance_deploy_dnsmasq import instance_deploy_dnsmasq
from zpodengine.instance_deploy.instance_deploy_networking import (
    instance_deploy_networking,
)
from zpodengine.instance_deploy.instance_deploy_prep import instance_deploy_prep
from zpodengine.instance_deploy.instance_deploy_vapp import instance_deploy_vapp


@flow(
    name="instance_deploy",
    flow_run_name="deploy_{instance_name}",
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
    mod.instance_profile_flow(instance_id=instance_id, wait_for=[vapp])


if __name__ == "__main__":
    flow_instance_deploy(
        instance_id=3,
        profile="sddc",
        instance_name="abc",
    )
