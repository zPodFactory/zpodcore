from typing import Any

from prefect import task
from sqlmodel import SQLModel

from zpodcommon import models as M
from zpodcommon.enums import InstanceComponentStatus
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
def instance_component_add_prep(
    keys: dict[str, str | int | None],
    data: dict[str, Any],
    label: str,
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
