from fastapi import HTTPException, status
from sqlmodel import SQLModel, select

from zpodapi.instances.instance_component__schemas import InstanceComponentCreate
from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class InstanceComponentService(ServiceBase):
    base_model: SQLModel = M.InstanceComponent

    def add(
        self,
        *,
        instance: M.Instance,
        component_in: InstanceComponentCreate,
    ):
        hostname = component_in.hostname
        if not hostname:
            # if hostname is not provided, look up default value
            component = self.session.exec(
                select(M.Component).where(
                    M.Component.component_uid == component_in.component_uid,
                    M.Component.status == ComponentStatus.ACTIVE,
                )
            ).one()
            hostname = component.component_name

        # if hostname is already found, raise error
        if self.session.exec(
            select(M.InstanceComponent).where(
                M.InstanceComponent.instance_id == instance.id,
                M.InstanceComponent.hostname == hostname,
            )
        ).one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicting record found",
            )

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_component_add",
            deployment_name="instance_component_add",
            run_name=(f"{instance.name} adding {component_in.component_uid}"),
            instance_id=instance.id,
            instance_name=instance.name,
            component_uid=component_in.component_uid,
            host_id=component_in.host_id,
            hostname=component_in.hostname,
            vcpu=component_in.vcpu,
            vmem=component_in.vmem,
        )

    def remove(
        self,
        *,
        instance_component,
    ):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_component_remove",
            deployment_name="instance_component_remove",
            instance_component_id=instance_component.id,
        )
