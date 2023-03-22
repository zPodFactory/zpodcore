from typing import Any

from prefect import task


@task(task_run_name="{label}: finalize")
def instance_component_finalize(
    instance_component: dict[str, Any],
    label: str,
):
    print("Finalizing")
