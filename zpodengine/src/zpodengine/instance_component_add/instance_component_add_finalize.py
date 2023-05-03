from prefect import task

from zpodcommon.enums import InstanceComponentStatus
from zpodengine.instance_component_add.instance_component_add_utils import (
    set_instance_component_status,
)


@task(task_run_name="{label}: finalize")
def instance_component_add_finalize(
    keys: dict[str, str | int | None],
    label: str,
):
    print("Finalizing")
    set_instance_component_status(keys, InstanceComponentStatus.ACTIVE)
