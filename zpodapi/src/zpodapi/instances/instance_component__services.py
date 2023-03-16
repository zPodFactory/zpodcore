from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from . import instance__utils


class InstanceService(ServiceBase):
    base_model: SQLModel = M.Instance

    def create(
        self,
        *,
        item_in: SQLModel,
        current_user: M.User,
        _model: SQLModel | None = None,
    ):
        return super()._create(
            _model=_model,
            item_in=item_in,
            extra=dict(
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


class InstanceComponentService(ServiceBase):
    base_model: SQLModel = M.InstanceComponent


class InstanceFeatureService(ServiceBase):
    base_model: SQLModel = M.InstanceFeature


class InstanceNetworkService(ServiceBase):
    base_model: SQLModel = M.InstanceNetwork
