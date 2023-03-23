import importlib

from prefect import flow

from zpodengine.instance.instance_dnsmasq import instance_dnsmasq
from zpodengine.instance.instance_networking import instance_networking
from zpodengine.instance.instance_prep import instance_prep
from zpodengine.instance.instance_vapp import instance_vapp


@flow(
    flow_run_name="deploy_{instance_name}",
    log_prints=True,
)
def flow_deploy_instance(
    instance_id: int,
    profile: str,
    instance_name: str,
):
    # Prep
    prep = instance_prep.submit(
        instance_id=instance_id,
        instance_name=instance_name,
    )

    # Create instance vapp
    vapp = instance_vapp.submit(
        instance_name=instance_name,
        wait_for=[prep],
    )

    # Configure DNSMASQ
    dnsmasq = instance_dnsmasq.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[vapp],
    )

    # Configure Top Level Networking
    networking = instance_networking.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[dnsmasq],
    )

    # # Deploy profile components
    mod = importlib.import_module(f"zpodengine.instance_profiles.{profile}")
    mod.instance_profile_flow(instance_id=instance_id, wait_for=[networking])


if __name__ == "__main__":
    flow_deploy_instance(
        instance_id=3,
        profile="sddc",
        instance_name="abc",
    )
