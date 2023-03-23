from typing import Any

from prefect import task


@task(task_run_name="{label}: execute pre_scripts")
def instance_component_pre_scripts(
    instance_component: dict[str, Any],
    label: str,
):
    custom_prescripts = instance_component.get("data", {}).get("prescripts", [])
    print(f"Run Prescripts: {custom_prescripts}")
