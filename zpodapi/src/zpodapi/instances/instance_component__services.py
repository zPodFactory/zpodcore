from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class InstanceComponentService(ServiceBase):
    base_model: SQLModel = M.InstanceComponent

    def add(
        self,
        *,
        instance_id: int,
        component_uid: str,
    ):
        return self.crud.create(
            item_in=M.InstanceComponent(
                instance_id=instance_id,
                component_uid=component_uid,
            )
        )
