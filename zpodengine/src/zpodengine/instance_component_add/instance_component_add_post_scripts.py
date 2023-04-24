from typing import Any

from prefect import task


@task(task_run_name="{label}: execute post_scripts")
def instance_component_add_post_scripts(
    instance_component: dict[str, Any],
    label: str,
):
    custom_postscripts = instance_component.get("data", {}).get("postscripts", [])
    print(f"Run Postscripts: {custom_postscripts}")
