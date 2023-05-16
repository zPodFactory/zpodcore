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
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_component_add",
            deployment_name="default",
            run_name=(f"For {instance.name} add {component_in.component_uid}"),
            instance_id=instance.id,
            instance_name=instance.name,
            component_uid=component_in.component_uid,
            data=component_in.data.dict(exclude_unset=True),
        )
