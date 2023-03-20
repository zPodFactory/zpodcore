import time

from prefect import flow, task

sleep = 2


@task(task_run_name="{label}: prep")
def instance_component_prep(label):
    time.sleep(sleep)


@task(task_run_name="{label}: pre_scripts")
def instance_component_pre_scripts(label):
    time.sleep(sleep)


@task(task_run_name="{label}: deploy")
def instance_component_deploy(label):
    time.sleep(sleep)


@task(task_run_name="{label}: post_scripts")
def instance_component_post_scripts(label):
    time.sleep(sleep)


@task(task_run_name="{label}: finalize")
def instance_component_finalize(label):
    time.sleep(sleep)


def deploy_component(instance_id: int, component_uid: str, wait_for=None):
    config = instance_component_prep.submit(component_uid, wait_for=wait_for)

    label = component_uid

    pre_scripts = instance_component_pre_scripts.submit(label, wait_for=config)
    package = instance_component_deploy.submit(label, wait_for=pre_scripts)
    post_scripts = instance_component_post_scripts.submit(label, wait_for=package)
    return instance_component_finalize.submit(label, wait_for=post_scripts)


@flow(
    log_prints=True,
)
def deploy_component_flow(
    instance_id: int,
    component_uid: str,
):
    vcsa = deploy_component(instance_id, "vcsa-8.0.0")
    nsxt = deploy_component(instance_id, "nsxt-4.3.1", wait_for=vcsa)
    esxis = [
        deploy_component(instance_id, f"esxi-8.0.0 [{x}]", wait_for=nsxt)
        for x in range(11, 14)
    ]
    hcx = deploy_component(instance_id, "hcx-2.6.3", wait_for=esxis)


if __name__ == "__main__":
    print(deploy_component_flow(1, "cds-10.2"))
