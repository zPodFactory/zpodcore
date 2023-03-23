from typing import Any

from prefect import task


@task(task_run_name="{label}: deploy")
def instance_component_deploy(
    instance_component: dict[str, Any],
    label: str,
):
    print("Deploy OVA")
