from fastapi import HTTPException, status

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import EndpointPermission


class EndpointPermissionService(ServiceBase):
    def user_add(
        self,
        *,
        endpoint: M.Endpoint,
        permission: EndpointPermission,
        user: M.User,
    ):
        # Remove user from all permissions
        for perm in endpoint.permissions:
            for perm_user in perm.users:
                if perm_user.id == user.id:
                    perm.users.remove(perm_user)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in endpoint.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.EndpointPermission(
                permission=permission,
                endpoint_id=endpoint.id,
            )

        # Add user to permission
        perm.users.append(user)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def user_remove(
        self,
        *,
        endpoint: M.Endpoint,
        permission: EndpointPermission,
        user: M.User,
    ):
        if perm := next(
            (x for x in endpoint.permissions if x.permission == permission), None
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
        endpoint: M.Endpoint,
        permission: EndpointPermission,
        group: M.PermissionGroup,
    ):
        # Remove group from all permissions
        for perm in endpoint.permissions:
            for perm_group in perm.permission_groups:
                if perm_group.id == group.id:
                    perm.permission_groups.remove(perm_group)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in endpoint.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.EndpointPermission(
                permission=permission.value,
                endpoint_id=endpoint.id,
            )

        # Add group to permission
        perm.permission_groups.append(group)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def group_remove(
        self,
        *,
        endpoint: M.Endpoint,
        permission: EndpointPermission,
        group: M.PermissionGroup,
    ):
        if perm := next(
            (x for x in endpoint.permissions if x.permission == permission), None
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
