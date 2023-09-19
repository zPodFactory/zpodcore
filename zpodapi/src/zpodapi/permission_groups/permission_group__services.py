from fastapi import HTTPException, status
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M


class PermissionGroupService(ServiceBase):
    base_model: SQLModel = M.PermissionGroup

    def user_add(
        self,
        *,
        permission_group: M.PermissionGroup,
        user_id: int,
    ):
        if not (user := self.session.get(M.User, user_id)):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found",
            )

        permission_group.users.append(user)
        self.session.add(permission_group)
        self.session.commit()
        return permission_group.users

    def user_delete(
        self,
        *,
        permission_group: M.PermissionGroup,
        user_id: int,
    ):
        for user in permission_group.users:
            if user.id == user_id:
                permission_group.users.remove(user)
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found",
            )
        self.session.commit()
