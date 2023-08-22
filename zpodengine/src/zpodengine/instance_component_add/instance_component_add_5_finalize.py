from prefect import task

from zpodcommon.enums import InstanceComponentStatus
from zpodengine.instance_component_add.instance_component_add_utils import (
    handle_instance_component_add_failure,
    set_instance_component_status,
)


@task
@handle_instance_component_add_failure
def instance_component_add_finalize(*, instance_component_id: int):
    print("Finalizing")
    set_instance_component_status(instance_component_id, InstanceComponentStatus.ACTIVE)
