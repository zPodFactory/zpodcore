from prefect import task

from zpodcommon.enums import ZpodComponentStatus
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
    set_zpod_component_status,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_finalize(*, zpod_component_id: int):
    print("Finalizing")
    set_zpod_component_status(zpod_component_id, ZpodComponentStatus.ACTIVE)
