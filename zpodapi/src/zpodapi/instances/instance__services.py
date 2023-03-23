from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.lib import zpodengine

from . import instance__utils
from .instance__enums import InstanceStatusEnum
from .instance__schemas import InstanceDelete


class InstanceService(ServiceBase):
    base_model: SQLModel = M.Instance

    def create(
        self,
        *,
        item_in: SQLModel,
        current_user: M.User,
        _model: SQLModel | None = None,
    ):
        instance = super()._create(
            _model=_model,
            item_in=item_in,
            extra=dict(
                status=InstanceStatusEnum.PENDING,
                password=instance__utils.gen_password(),
                permissions=[
                    M.InstancePermission(
                        name="Owner",
                        permission="zpodadmin",
                        users=[current_user],
                    )
                ],
            ),
        )
        zpod_engine = zpodengine.ZpodEngine()
        zpod_engine.create_flow_run_by_name(
            flow_name="flow-deploy-instance",
            deployment_name="default",
            instance_id=instance.id,
            profile=instance.profile,
            instance_name=instance.name,
        )
        return instance

    def delete(self, *, item: SQLModel):
        self.update(
            item=item,
            item_in=InstanceDelete(status=InstanceStatusEnum.DELETED),
        )
        return None
