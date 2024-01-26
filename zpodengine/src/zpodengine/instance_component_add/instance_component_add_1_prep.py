from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, InstanceComponentStatus
from zpodcommon.lib.network import MgmtIp
from zpodengine.lib import database


@task(persist_result=True)
def instance_component_add_prep(
    instance_id: int,
    component_uid: str,
    host_id: int | None = None,
    hostname: str | None = None,
):
    with database.get_session_ctx() as session:
        component = session.exec(
            select(M.Component).where(
                M.Component.component_uid == component_uid,
                M.Component.status == ComponentStatus.ACTIVE,
            )
        ).one()
        instance = session.get(M.Instance, instance_id)

        if not hostname:
            hostname = component.component_name

        instance_component = M.InstanceComponent(
            instance_id=instance_id,
            component_id=component.id,
            ip=MgmtIp.instance(
                instance,
                host_id=host_id,
                component_name=component.component_name,
            ).ip,
            hostname=hostname,
            fqdn=f"{hostname}.{instance.domain}",
            status=InstanceComponentStatus.BUILDING,
        )

        session.add(instance_component)
        session.commit()
        session.refresh(instance_component)
    return instance_component
