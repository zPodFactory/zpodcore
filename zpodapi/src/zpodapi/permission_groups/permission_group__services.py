from fastapi import HTTPException, status
from sqlmodel import SQLModel
from zpodcommon import models as M

from zpodapi.lib.service_base import ServiceBase


class PermissionGroupService(ServiceBase):
    base_model: SQLModel = M.PermissionGroup

    def user_add(
        self,
        *,
        permission_group: M.PermissionGroup,
        user_id: int,
    ):
        for _user in permission_group.users:
            if _user.id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already in group",
                )

        if not (user := self.session.get(M.User, user_id)):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found in group",
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
                detail="User not found in group",
            )
        self.session.commit()

    def get_permission_group_record(self, group_id, groupname):
        if (group_id and groupname) or (not group_id and not groupname):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Must provide group_id or groupname",
            )
        elif group_id and not (group := self.session.get(M.PermissionGroup, group_id)):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Group not found",
            )
        elif groupname and not (
            group := self.crud.select(
                where=[M.PermissionGroup.name == groupname]
            ).one_or_none()
        ):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Group not found",
            )
        return group
