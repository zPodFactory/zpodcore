from typing import Any

from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, InstanceComponentStatus
from zpodengine.lib import database


@task(persist_result=True)
def instance_component_add_prep(
    instance_id: int,
    component_uid: str,
    data: dict[str, Any],
):  # sourcery skip: remove-unnecessary-cast
    with database.get_session_ctx() as session:
        component = session.exec(
            select(M.Component).where(
                M.Component.component_uid == component_uid,
                # Needs new status value
                M.Component.status == ComponentStatus.DOWNLOAD_COMPLETE,
            )
        ).one()
        instance_component = M.InstanceComponent(
            instance_id=instance_id,
            component_id=component.id,
            data=data,
            status=InstanceComponentStatus.BUILDING,
        )
        session.add(instance_component)
        session.commit()
        session.refresh(instance_component)
    return instance_component.id
