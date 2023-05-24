from sqlalchemy import func
from sqlmodel import or_, select

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import enums
from zpodcommon import models as M
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from . import instance__utils
from .instance__schemas import InstanceCreate


class InstanceService(ServiceBase):
    base_model: M.Instance = M.Instance

    def get_all(self):
        return self.get_instance_records(
            where_user=True,
            where=[M.Instance.status.not_in([enums.InstanceStatus.DELETED.value])],
        ).all()

    def get(self, *, id=None, name=None, name_insensitive=None):
        where = []
        if id:
            where.append(M.Instance.id == id),
        elif name or name_insensitive:
            if name:
                where.append(M.Instance.name == name)
            else:
                where.append(func.lower(M.Instance.name) == name_insensitive.lower())
            where.append(M.Instance.status.not_in([enums.InstanceStatus.DELETED.value]))
        else:
            return None
        return self.get_instance_records(where_user=True, where=where).one_or_none()

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
            run_name=f"Deploy {instance.name}",
            instance_id=instance.id,
            profile=instance.profile,
            instance_name=instance.name,
        )

        # Only commit if zpodengine flow scheduled properly
        self.session.commit()
        return instance

    def delete(self, *, instance: M.Instance):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_destroy",
            deployment_name="default",
            run_name=f"Destroy {instance.name}",
            instance_id=instance.id,
            instance_name=instance.name,
        )
        return None

    def get_instance_records(
        self,
        select_fields=M.Instance,
        where_user=True,
        where=None,
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
        if where_user and not self.is_superadmin:
            stmt = stmt.where(
                or_(
                    M.InstancePermissionUserLink.user_id == self.current_user.id,
                    M.PermissionGroupUserLink.user_id == self.current_user.id,
                )
            )
        if where:
            stmt = stmt.where(*where)
        if order_by:
            stmt = stmt.order_by(order_by)
        return self.session.exec(stmt)

    def get_user_instance_permissions(self, user_id: int, instance_id: int) -> set[str]:
        permissions = self.get_instance_records(
            select_fields=M.InstancePermission.permission,
            where_user=True,
            where=[M.Instance.id == id],
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
