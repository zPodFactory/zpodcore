from fastapi import HTTPException, status
from rich import print
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import SQLModel, or_, select

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import EndpointStatus, ZpodStatus

from .endpoint__schemas import EndpointUpdate
from .endpoint__utils import update_dictionary, zpod_endpoint_check


class EndpointService(ServiceBase):
    base_model: SQLModel = M.Endpoint

    def get_all(self):
        return self.get_endpoint_records(
            where=[
                M.Endpoint.status == EndpointStatus.ACTIVE,
            ]
        ).all()

    def get(self, *, id=None, name=None, name_insensitive=None):
        where = []
        if id:
            where.append(
                M.Endpoint.id == id,
                M.Endpoint.status == EndpointStatus.ACTIVE,
            )
        elif name or name_insensitive:
            if name:
                where.append(M.Endpoint.name == name)
            else:
                where.append(func.lower(M.Endpoint.name) == name_insensitive.lower())
            where.append(M.Endpoint.status == EndpointStatus.ACTIVE)
        else:
            return None
        return self.get_endpoint_records(where=where).one_or_none()

    def update(self, *, item: M.Endpoint, item_in: EndpointUpdate):
        for key, value in item_in.model_dump(exclude_unset=True).items():
            # specific code to handle nested dictionaries & JSON fields
            if key == "endpoints":
                update_dictionary(item.endpoints, value)
                value = item.endpoints

            setattr(item, key, value)

        # https://stackoverflow.com/questions/42559434/updates-to-json-field-dont-persist-to-db
        flag_modified(item, "endpoints")
        self.crud.save(item)
        return item

    def delete(self, *, item: M.Endpoint):
        stmt = select(func.count()).where(
            M.Zpod.endpoint_id == item.id,
            M.Zpod.status.in_(
                [
                    ZpodStatus.ACTIVE,
                    ZpodStatus.BUILDING,
                    ZpodStatus.PENDING,
                    ZpodStatus.DELETING,
                ]
            ),
        )
        if self.session.exec(stmt).one():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Endpoint in use",
            )
        item.status = EndpointStatus.DELETED
        self.crud.save(item)

    def verify(self, *, item: M.Endpoint):
        # Verify endpoint status
        print(f"Verifying Endpoint {item.name}")
        return zpod_endpoint_check(item)

    def get_endpoint_records(
        self,
        select_fields=M.Endpoint,
        where=None,
        order_by=M.Endpoint.name,
    ):
        stmt = select(select_fields).select_from(M.Endpoint)
        if not self.is_superadmin:
            stmt = (
                stmt.join(M.EndpointPermission)
                .outerjoin(M.EndpointPermissionUserLink)
                .outerjoin(M.EndpointPermissionGroupLink)
                .outerjoin(M.PermissionGroup)
                .outerjoin(M.PermissionGroupUserLink)
                .where(
                    or_(
                        M.EndpointPermissionUserLink.user_id == self.current_user.id,
                        M.PermissionGroupUserLink.user_id == self.current_user.id,
                    )
                )
            )

        if where:
            stmt = stmt.where(*where)
        if order_by:
            stmt = stmt.order_by(order_by)
        return self.session.exec(stmt)

    def get_user_endpoint_permissions(self, endpoint_id: int) -> set[str]:
        permissions = self.get_endpoint_records(
            select_fields=M.EndpointPermission.permission,
            where=[M.Endpoint.id == endpoint_id],
            order_by=None,
        ).all()
        return set(permissions)
