from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, ZpodComponentStatus
from zpodengine.lib import database
from zpodengine.lib.network import MgmtIp


@task(persist_result=True)
def zpod_component_add_prep(
    zpod_id: int,
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
        zpod = session.get(M.Zpod, zpod_id)

        if not hostname:
            hostname = component.component_name

        zpod_component = M.ZpodComponent(
            zpod_id=zpod_id,
            component_id=component.id,
            ip=MgmtIp.zpod(
                zpod,
                host_id=host_id,
                component_name=component.component_name,
            ).ip,
            hostname=hostname,
            fqdn=f"{hostname}.{zpod.domain}",
            status=ZpodComponentStatus.BUILDING,
        )

        session.add(zpod_component)
        session.commit()
        session.refresh(zpod_component)
    return zpod_component
