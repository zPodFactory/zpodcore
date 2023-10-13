from fastapi import HTTPException, status
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import InstancePermission


class InstancePermissionService(ServiceBase):
    base_model: SQLModel = M.InstanceComponent

    def user_add(
        self,
        *,
        instance: M.Instance,
        permission: InstancePermission,
        user: M.User,
    ):
        # Remove user from all permissions
        for perm in instance.permissions:
            for perm_user in perm.users:
                if perm_user.id == user.id:
                    perm.users.remove(perm_user)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in instance.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.InstancePermission(
                permission=permission.value,
                instance_id=instance.id,
            )

        # Add user to permission
        perm.users.append(user)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def user_remove(
        self,
        *,
        instance: M.Instance,
        permission: InstancePermission,
        user: M.User,
    ):
        if perm := next(
            (x for x in instance.permissions if x.permission == permission), None
        ):
            for perm_user in perm.users:
                if perm_user.id == user.id:
                    perm.users.remove(perm_user)
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"User not found in permission: {permission}",
                )
            if not perm.users and not perm.permission_groups:
                self.session.delete(perm)
            self.session.commit()

    def group_add(
        self,
        *,
        instance: M.Instance,
        permission: InstancePermission,
        group: M.PermissionGroup,
    ):
        # Remove group from all permissions
        for perm in instance.permissions:
            for perm_group in perm.permission_groups:
                if perm_group.id == group.id:
                    perm.permission_groups.remove(perm_group)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in instance.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.InstancePermission(
                permission=permission.value,
                instance_id=instance.id,
            )

        # Add group to permission
        perm.permission_groups.append(group)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def group_remove(
        self,
        *,
        instance: M.Instance,
        permission: InstancePermission,
        group: M.PermissionGroup,
    ):
        if perm := next(
            (x for x in instance.permissions if x.permission == permission), None
        ):
            for perm_group in perm.permission_groups:
                if perm_group.id == group.id:
                    perm.permission_groups.remove(perm_group)
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"Group not found in permission: {permission}",
                )
            if not perm.users and not perm.permission_groups:
                self.session.delete(perm)
            self.session.commit()
