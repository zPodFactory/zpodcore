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
        instance_id: int,
        component_in: InstanceComponentCreate,
    ):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_component_add",
            deployment_name="default",
            instance_id=instance_id,
            component_uid=component_in.component_uid,
            extra_id=component_in.extra_id,
            data=component_in.data,
        )
