from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import enums
from zpodcommon import models as M
from zpodcommon.lib.zpodengine import ZpodEngine

from . import instance__utils
from .instance__schemas import InstanceCreate, InstanceDelete

EXTRA_CRITERIA = [
    M.Instance.status.in_(
        [
            enums.InstanceStatus.ACTIVE.value,
            enums.InstanceStatus.PENDING.value,
        ]
    )
]


class InstanceService(ServiceBase):
    base_model: SQLModel = M.Instance

    def get_all(
        self,
        *,
        name: str | None = None,
    ):
        return self.crud.get_all_filtered(
            extra_criteria=EXTRA_CRITERIA,
            name=name,
        )

    def get(self, *, id=None, name=None):
        return self.crud.get(
            extra_criteria=EXTRA_CRITERIA if id is None else None,
            id=id,
            name=name,
        )

    def create(
        self,
        *,
        item_in: InstanceCreate,
        current_user: M.User,
    ):
        instance = self.crud.create(
            item_in=item_in,
            extra=dict(
                status=enums.InstanceStatus.PENDING,
                password=instance__utils.gen_password(),
                permissions=[
                    M.InstancePermission(
                        permission="zpodowner",
                        users=[current_user],
                    )
                ],
            ),
        )
        zpod_engine = ZpodEngine()
        zpod_engine.create_flow_run_by_name(
            flow_name="flow-deploy-instance",
            deployment_name="default",
            instance_id=instance.id,
            profile=instance.profile,
            instance_name=instance.name,
        )
        return instance

    def delete(self, *, instance: SQLModel):
        self.crud.update(
            item=instance,
            item_in=InstanceDelete(status=enums.InstanceStatus.DELETED),
        )
        return None
