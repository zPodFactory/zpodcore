from typing import Any

from prefect import task
from sqlmodel import SQLModel

from zpodcommon import models as M
from zpodengine.lib import database


class ComponentView(SQLModel):
    component_uid: str
    component_name: str
    component_version: str
    library_name: str
    filename: str
    enabled: bool
    status: str


class InstanceComponentView(SQLModel):
    instance_id: int
    component: ComponentView
    data: dict[Any, Any]
    extra_id: str


@task(task_run_name="{label}: prep")
def instance_component_prep(
    instance_id: int,
    component_uid: str,
    extra_id: str,
    data: dict[str, Any],
    label: str,
):
    with database.get_session_ctx() as session:
        instance_component = M.InstanceComponent(
            instance_id=instance_id,
            component_uid=component_uid,
            extra_id=extra_id,
            data=data,
        )

        session.add(instance_component)
        session.commit()
        session.refresh(instance_component)
        return InstanceComponentView.from_orm(instance_component).dict()
