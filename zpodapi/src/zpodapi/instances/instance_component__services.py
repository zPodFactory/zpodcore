from sqlmodel import SQLModel

from zpodapi.instances.instance_component__schemas import InstanceComponentCreate
from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class InstanceComponentService(ServiceBase):
    base_model: SQLModel = M.InstanceComponent

    def add(
        self,
        *,
        instance: M.Instance,
        component_in: InstanceComponentCreate,
    ):
        zpod_engine = ZpodEngineClient()

        profile_item = dict(component_uid=component_in.component_uid)
        profile_item |= component_in.data.dict()

        zpod_engine.create_flow_run_by_name(
            flow_name="instance_component_add",
            deployment_name="default",
            run_name=(f"{instance.name} adding {component_in.component_uid}"),
            instance_id=instance.id,
            instance_name=instance.name,
            profile_item=profile_item,
        )
