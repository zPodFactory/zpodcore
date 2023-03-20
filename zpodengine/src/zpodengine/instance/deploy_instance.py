import importlib
import time

from prefect import flow, task

sleep = 1


@task(task_run_name="{instance_name}: create vapp")
def create_instance_vapp(instance_name: str):
    time.sleep(sleep)


@task(task_run_name="{instance_name}: configure dnsmasq")
def configure_instance_dnsmasq(instance_name: str):
    time.sleep(sleep)


@task(task_run_name="{instance_name}: configure top level networking")
def configure_instance_networking(instance_name: str):
    time.sleep(sleep)


@flow(
    flow_run_name="deploy_{instance_name}",
    log_prints=True,
)
def deploy_instance(
    instance_id: int,
    profile: str,
    instance_name: str,
):
    # Create instance vapp
    instance_vapp = create_instance_vapp.submit(
        instance_name=instance_name,
    )

    # Configure DNSMASQ
    instance_dnsmasq = configure_instance_dnsmasq.submit(
        instance_name=instance_name,
        wait_for=instance_vapp,
    )

    # Configure NSX
    instance_networking = configure_instance_networking.submit(
        instance_name=instance_name,
        wait_for=instance_dnsmasq,
    )

    # Deploy profile components
    mod = importlib.import_module(f"zpodengine.instance_profiles.{profile}")
    mod.instance_profile_flow(instance_id=instance_id, wait_for=instance_networking)


if __name__ == "__main__":
    deploy_instance(
        instance_id=1,
        profile="sddc",
        instance_name="abc",
    )
