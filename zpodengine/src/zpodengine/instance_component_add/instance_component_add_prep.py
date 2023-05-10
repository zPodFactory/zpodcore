from typing import Any

from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import InstanceComponentStatus
from zpodengine.lib import database


@task
def instance_component_add_prep(
    keys: dict[str, str | int | None],
    data: dict[str, Any],
):
    with database.get_session_ctx() as session:
        instance_component = M.InstanceComponent(
            **keys,
            data=data,
            status=InstanceComponentStatus.BUILDING,
        )
        session.add(instance_component)
        session.commit()
        session.refresh(instance_component)
