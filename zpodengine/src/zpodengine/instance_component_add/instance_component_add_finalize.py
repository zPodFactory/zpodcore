from prefect import task

from zpodcommon.enums import InstanceComponentStatus
from zpodengine.instance_component_add.instance_component_add_utils import (
    set_instance_component_status,
)


@task
def instance_component_add_finalize(keys: dict[str, str | int | None]):
    print("Finalizing")
    set_instance_component_status(keys, InstanceComponentStatus.ACTIVE)
