from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, ZpodComponentStatus
from zpodcommon.lib.network_utils import (
    MgmtIp,
    get_all_active_addresses,
    get_zpod_reserved_addresses,
)
from zpodengine.lib import database


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

        component_ip = MgmtIp.zpod(
            zpod,
            host_id=host_id,
            component_name=component.component_name,
        ).ipv4address

        if component_ip in get_zpod_reserved_addresses(zpod):
            raise ValueError(
                f"Invalid IP: {component_ip}.  Specified IP is a reserved IP."
            )
        if component_ip in get_all_active_addresses(zpod):
            raise ValueError(
                f"Invalid IP: {component_ip}.  Specified IP is already in use."
            )
        zpod_component = M.ZpodComponent(
            zpod_id=zpod_id,
            component_id=component.id,
            ip=component_ip,
            hostname=hostname,
            fqdn=f"{hostname}.{zpod.domain}",
            status=ZpodComponentStatus.BUILDING,
        )

        session.add(zpod_component)
        session.commit()
        session.refresh(zpod_component)
    return zpod_component
