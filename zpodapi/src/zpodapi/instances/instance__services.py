from sqlmodel import SQLModel, or_, select

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import enums
from zpodcommon import models as M
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from . import instance__utils
from .instance__schemas import InstanceCreate

ACTIVE_STATUSES = [
    enums.InstanceStatus.ACTIVE.value,
    enums.InstanceStatus.PENDING.value,
]


class InstanceService(ServiceBase):
    base_model: SQLModel = M.Instance

    def get_all(self):
        return self.get_instance_records(
            user_id=None if self.is_superadmin else self.current_user.id,
            statuses=ACTIVE_STATUSES,
        ).all()

    def get(self, *, id=None, name=None):
        user_id = None if self.is_superadmin else self.current_user.id
        if id:
            records = self.get_instance_records(
                user_id=user_id,
                instance_id=id,
            )
        if name:
            records = self.get_instance_records(
                user_id=user_id,
                name=name,
                statuses=ACTIVE_STATUSES,
            )
        return records.one_or_none()

    def create(
        self,
        *,
        item_in: InstanceCreate,
        current_user: M.User,
    ):
        instance = M.Instance(
            **item_in.dict(),
            status=enums.InstanceStatus.PENDING,
            password=instance__utils.gen_password(),
            permissions=[
                M.InstancePermission(
                    permission=enums.InstancePermission.INSTANCE_OWNER,
                    users=[current_user],
                )
            ],
        )
        self.session.add(instance)
        self.session.flush()

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_deploy",
            deployment_name="default",
            instance_id=instance.id,
            profile=instance.profile,
            instance_name=instance.name,
        )

        # Only commit if zpodengine flow scheduled properly
        self.session.commit()
        return instance

    def delete(self, *, instance: SQLModel):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_destroy",
            deployment_name="default",
            instance_id=instance.id,
            instance_name=instance.name,
        )
        return None

    def get_instance_records(
        self,
        select_fields=M.Instance,
        name: str | None = None,
        user_id: int | None = None,
        instance_id: int | None = None,
        permissions: list[str] | None = None,
        statuses: list[str] | None = None,
        order_by=M.Instance.name,
    ):
        stmt = (
            select(select_fields)
            .select_from(M.Instance)
            .distinct()
            .join(M.InstancePermission)
            .outerjoin(M.InstancePermissionUserLink, full=True)
            .outerjoin(M.InstancePermissionGroupLink, full=True)
            .outerjoin(M.PermissionGroup, full=True)
            .outerjoin(M.PermissionGroupUserLink, full=True)
        )
        if user_id:
            stmt = stmt.where(
                or_(
                    M.InstancePermissionUserLink.user_id == user_id,
                    M.PermissionGroupUserLink.user_id == user_id,
                )
            )
        if name:
            stmt = stmt.where(M.Instance.name == name)
        if instance_id:
            stmt = stmt.where(M.Instance.id == instance_id)
        if permissions:
            stmt = stmt.where(M.InstancePermission.permission.in_(permissions))
        if statuses:
            stmt = stmt.where(M.Instance.status.in_(statuses))
        if order_by:
            stmt = stmt.order_by(order_by)
        return self.session.exec(stmt)

    def get_user_instance_permissions(self, user_id: int, instance_id: int) -> set[str]:
        permissions = self.get_instance_records(
            select_fields=M.InstancePermission.permission,
            user_id=user_id,
            instance_id=instance_id,
            order_by=None,
        ).all()
        return set(permissions)

    def has_permission(self, user_id: int, instance_id: int, permissions: set[str]):
        user_permissions = self.get_user_instance_permissions(
            user_id=user_id,
            instance_id=instance_id,
        )
        return user_permissions.intersection(permissions)

    def is_readable(self, user_id: int, instance_id: int):
        return self.has_permission(
            user_id=user_id,
            instance_id=instance_id,
            permissions={
                enums.InstancePermission.INSTANCE_OWNER,
                enums.InstancePermission.INSTANCE_ADMIN,
                enums.InstancePermission.INSTANCE_READ_ONLY,
            },
        )

    def is_admin(self, user_id: int, instance_id: int):
        return self.has_permission(
            user_id=user_id,
            instance_id=instance_id,
            permissions={
                enums.InstancePermission.INSTANCE_OWNER,
                enums.InstancePermission.INSTANCE_ADMIN,
            },
        )
