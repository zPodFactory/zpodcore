import importlib

from prefect import flow, task

from zpodcommon import models as M
from zpodengine.lib import database

sleep = 1


def get_available_network():
    return "192.168.0.0/24"


@task(task_run_name="{instance_name}: prep")
def instance_prep(instance_id: int, instance_name: str):
    # Add default network
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        instance.networks.append(M.InstanceNetwork(cidr=get_available_network()))
        session.add(instance)
        session.commit()


@task(task_run_name="{instance_name}: create vapp")
def create_instance_vapp(
    instance_name: str,
):
    print("Create Instance VAPP")


@task(task_run_name="{instance_name}: configure dnsmasq")
def configure_instance_dnsmasq(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        print(f"Set DNSMASQ using the {instance.networks[0].cidr} network")


@task(task_run_name="{instance_name}: configure top level networking")
def configure_instance_networking(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        print(
            f"Configure top level networking with {instance.networks[0].cidr} network"
        )


@flow(
    flow_run_name="deploy_{instance_name}",
    log_prints=True,
)
def deploy_instance(
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
    instance_vapp = create_instance_vapp.submit(
        instance_name=instance_name,
        wait_for=[prep],
    )

    # Configure DNSMASQ
    instance_dnsmasq = configure_instance_dnsmasq.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[instance_vapp],
    )

    # Configure Top Level Networking
    instance_networking = configure_instance_networking.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[instance_dnsmasq],
    )

    # # Deploy profile components
    mod = importlib.import_module(f"zpodengine.instance_profiles.{profile}")
    mod.instance_profile_flow(instance_id=instance_id, wait_for=[instance_networking])


if __name__ == "__main__":
    deploy_instance(
        instance_id=2,
        profile="sddc",
        instance_name="abc",
    )
