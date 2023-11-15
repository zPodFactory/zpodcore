from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import or_, select

from zpodapi import settings
from zpodapi.lib.service_base import ServiceBase
from zpodcommon import enums
from zpodcommon import models as M
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from ..profiles.profile__utils import validate_profile
from . import instance__utils
from .instance__schemas import InstanceCreate


class InstanceService(ServiceBase):
    base_model: M.Instance = M.Instance

    def get_all(self):
        return self.get_instance_records(
            where=[M.Instance.status.not_in([enums.InstanceStatus.DELETED.value])],
        ).all()

    def get(self, *, id=None, name=None, name_insensitive=None):
        where = []
        if id:
            where.append(M.Instance.id == id)
        elif name or name_insensitive:
            if name:
                where.append(M.Instance.name == name)
            else:
                where.append(func.lower(M.Instance.name) == name_insensitive.lower())
            where.append(M.Instance.status.not_in([enums.InstanceStatus.DELETED.value]))
        else:
            return None
        return self.get_instance_records(where=where).one_or_none()

    def create(
        self,
        *,
        item_in: InstanceCreate,
        current_user: M.User,
    ):
        instance = M.Instance(
            name=item_in.name,
            description=item_in.description,
            domain=item_in.domain,
            endpoint_id=item_in.endpoint_id,
            profile=item_in.profile,
            status=enums.InstanceStatus.PENDING,
            password=instance__utils.gen_password(),
            permissions=[
                M.InstancePermission(
                    permission=enums.InstancePermission.OWNER,
                    users=[current_user],
                )
            ],
        )
        self.session.add(instance)
        self.session.flush()

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_deploy",
            deployment_name="instance_deploy",
            run_name=f"Deploy {instance.name}",
            instance_id=instance.id,
            enet_name=(
                f"{settings.SITE_ID}-{item_in.enet_name}-enet-project"
                if item_in.enet_name
                else None
            ),
            profile=instance.profile,
            instance_name=instance.name,
        )

        # Only commit if zpodengine flow scheduled properly
        self.session.commit()
        return instance

    def validate_profile(self, *, profile_name):
        if profile := self.session.exec(
            select(M.Profile).where(
                M.Profile.name == profile_name.lower(),
            )
        ).one_or_none():
            print(profile)
            validate_profile(session=self.session, profile_obj=profile.profile)
        else:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=f"Profile not found for name: {profile_name}",
            )

    def delete(self, *, instance: M.Instance):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="instance_destroy",
            deployment_name="instance_destroy",
            run_name=f"Destroy {instance.name}",
            instance_id=instance.id,
            instance_name=instance.name,
        )
        return None

    def get_instance_records(
        self,
        select_fields=M.Instance,
        where=None,
        order_by=M.Instance.name,
    ):
        stmt = select(select_fields).select_from(M.Instance)
        if not self.is_superadmin:
            stmt = (
                stmt.join(M.InstancePermission)
                .outerjoin(M.InstancePermissionUserLink)
                .outerjoin(M.InstancePermissionGroupLink)
                .outerjoin(M.PermissionGroup)
                .outerjoin(M.PermissionGroupUserLink)
                .where(
                    or_(
                        M.InstancePermissionUserLink.user_id == self.current_user.id,
                        M.PermissionGroupUserLink.user_id == self.current_user.id,
                    )
                )
            ).distinct()

        if where:
            stmt = stmt.where(*where)
        if order_by:
            stmt = stmt.order_by(order_by)
        return self.session.exec(stmt)
