from fastapi import HTTPException, status
from sqlmodel import SQLModel, select

from zpodapi.lib.service_base import ServiceBase
from zpodapi.zpods.zpod_component__schemas import ZpodComponentCreate
from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, ZpodComponentStatus
from zpodcommon.lib.network_utils import (
    MgmtIp,
    get_all_active_addresses,
    get_zpod_reserved_addresses,
)
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class ZpodComponentService(ServiceBase):
    base_model: SQLModel = M.ZpodComponent

    def add(
        self,
        *,
        zpod: M.Zpod,
        component_in: ZpodComponentCreate,
    ):
        hostname = component_in.hostname
        host_id = component_in.host_id

        if (hostname and not host_id) or (not hostname and host_id):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Must provide both hostname and host-id when either is provided.",  # noqa: E501
            )

        component = self.session.exec(
            select(M.Component).where(
                M.Component.component_uid == component_in.component_uid,
                M.Component.status == ComponentStatus.ACTIVE,
            )
        ).one()
        if not hostname:
            if component.component_name == "esxi":
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail="Must provide hostname and host-id when adding esxi.",
                )
            # if hostname is not provided, look up default value
            hostname = component.component_name

        # if hostname is already found, raise error
        if self.session.exec(
            select(M.ZpodComponent).where(
                M.ZpodComponent.zpod_id == zpod.id,
                M.ZpodComponent.hostname == hostname,
                M.ZpodComponent.status.in_(
                    [
                        ZpodComponentStatus.ACTIVE,
                        ZpodComponentStatus.BUILDING,
                    ]
                ),
            )
        ).one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicting hostname found",
            )

        component_ip = MgmtIp.zpod(
            zpod,
            host_id=host_id,
            component_name=component.component_name,
        ).ipv4address

        if component_ip in get_zpod_reserved_addresses(zpod):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid IP: {component_ip}.  Specified IP is a reserved IP.",
            )
        if component_ip in get_all_active_addresses(zpod):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid IP: {component_ip}.  Specified IP is already in use.",
            )

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_component_add",
            deployment_name="zpod_component_add",
            run_name=(f"{zpod.name} adding {component_in.component_uid}"),
            zpod_id=zpod.id,
            zpod_name=zpod.name,
            component_uid=component_in.component_uid,
            host_id=component_in.host_id,
            hostname=component_in.hostname,
            vcpu=component_in.vcpu,
            vmem=component_in.vmem,
            vnics=component_in.vnics,
            vdisks=component_in.vdisks,
        )

    def remove(
        self,
        *,
        zpod_component,
    ):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_component_remove",
            deployment_name="zpod_component_remove",
            zpod_component_id=zpod_component.id,
        )
