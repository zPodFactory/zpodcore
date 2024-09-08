from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import or_, select

from zpodapi import settings
from zpodapi.lib.service_base import ServiceBase
from zpodcommon import enums
from zpodcommon import models as M
from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from ..profiles.profile__utils import validate_profile
from . import zpod__utils
from .zpod__schemas import ZpodCreate


class ZpodService(ServiceBase):
    base_model: M.Zpod = M.Zpod

    def get_all(self):
        return self.get_zpod_records(
            where=[M.Zpod.status.not_in([enums.ZpodStatus.DELETED.value])],
        ).all()

    def get(self, *, id=None, name=None, name_insensitive=None):
        where = []
        if id:
            where.append(M.Zpod.id == id)
        elif name or name_insensitive:
            if name:
                where.append(M.Zpod.name == name)
            else:
                where.append(func.lower(M.Zpod.name) == name_insensitive.lower())
            where.append(M.Zpod.status.not_in([enums.ZpodStatus.DELETED.value]))
        else:
            return None
        return self.get_zpod_records(where=where).one_or_none()

    def create(
        self,
        *,
        item_in: ZpodCreate,
        current_user: M.User,
    ):
        # FF (Feature Flag) support for unique password
        zpod_password = (
            DBUtils.get_setting_value("ff_unique_zpod_password")
            or zpod__utils.gen_password()
        )

        zpod = M.Zpod(
            name=item_in.name,
            description=item_in.description,
            domain=item_in.domain,
            endpoint_id=item_in.endpoint_id,
            profile=item_in.profile,
            status=enums.ZpodStatus.PENDING,
            password=zpod_password,
            permissions=[
                M.ZpodPermission(
                    permission=enums.ZpodPermission.OWNER,
                    users=[current_user],
                )
            ],
        )
        self.session.add(zpod)
        self.session.flush()

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_deploy",
            deployment_name="zpod_deploy",
            run_name=f"Deploy {zpod.name}",
            zpod_id=zpod.id,
            enet_name=(
                f"{settings.SITE_ID}-{item_in.enet_name}-enet-project"
                if item_in.enet_name
                else None
            ),
            profile=zpod.profile,
            zpod_name=zpod.name,
        )

        # Only commit if zpodengine flow scheduled properly
        self.session.commit()
        return zpod

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

    def delete(self, *, zpod: M.Zpod):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_destroy",
            deployment_name="zpod_destroy",
            run_name=f"Destroy {zpod.name}",
            zpod_id=zpod.id,
            zpod_name=zpod.name,
        )
        return None

    def get_zpod_records(
        self,
        select_fields=M.Zpod,
        where=None,
        order_by=M.Zpod.name,
    ):
        stmt = select(select_fields).select_from(M.Zpod)
        if not self.is_superadmin:
            stmt = (
                stmt.join(M.ZpodPermission)
                .outerjoin(M.ZpodPermissionUserLink)
                .outerjoin(M.ZpodPermissionGroupLink)
                .outerjoin(M.PermissionGroup)
                .outerjoin(M.PermissionGroupUserLink)
                .where(
                    or_(
                        M.ZpodPermissionUserLink.user_id == self.current_user.id,
                        M.PermissionGroupUserLink.user_id == self.current_user.id,
                    )
                )
            ).distinct()

        if where:
            stmt = stmt.where(*where)
        if order_by:
            stmt = stmt.order_by(order_by)
        return self.session.exec(stmt)
