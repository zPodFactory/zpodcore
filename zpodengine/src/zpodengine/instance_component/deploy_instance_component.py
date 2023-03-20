import time

from prefect import flow, task

sleep = 1


@task(task_run_name="{label}: prep")
def instance_component_prep(label):
    time.sleep(sleep)


@task(task_run_name="{label}: execute pre_scripts")
def instance_component_pre_scripts(label):
    time.sleep(sleep)


@task(task_run_name="{label}: deploy")
def instance_component_deploy(label):
    time.sleep(sleep)


@task(task_run_name="{label}: execute post_scripts")
def instance_component_post_scripts(label):
    time.sleep(sleep)


@task(task_run_name="{label}: finalize")
def instance_component_finalize(label):
    time.sleep(sleep)


def deploy_instance_component(instance_id: int, component_uid: str, wait_for=None):
    prep = instance_component_prep.submit(component_uid, wait_for=wait_for)
    label = component_uid
    pre_scripts = instance_component_pre_scripts.submit(label, wait_for=prep)
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
    deploy_instance_component(instance_id=instance_id, component_uid=component_uid)


if __name__ == "__main__":
    print(deploy_component_flow(1, "cds-10.2"))
