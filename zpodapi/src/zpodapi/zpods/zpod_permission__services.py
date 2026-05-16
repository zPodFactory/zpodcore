from fastapi import HTTPException, status
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ZpodPermission

# Permission levels that keep a zPod manageable by a non-superadmin.
_MAINTAINER_LEVELS = (ZpodPermission.OWNER, ZpodPermission.ADMIN)


def _remaining_maintainer_user_ids(
    zpod: M.Zpod,
    *,
    excluding_user_id: int | None = None,
    excluding_group_id: int | None = None,
) -> set[int]:
    """User ids still holding OWNER/ADMIN on `zpod` once the excluded principal
    is removed (direct grants + permission-group membership).

    `excluding_user_id` only drops direct grants; a user still reachable via a
    permission group is correctly counted, mirroring what `user_remove` mutates.
    """
    ids: set[int] = set()
    for perm in zpod.permissions:
        if perm.permission not in _MAINTAINER_LEVELS:
            continue
        for user in perm.users:
            if user.id != excluding_user_id:
                ids.add(user.id)
        for group in perm.permission_groups:
            if group.id == excluding_group_id:
                continue
            ids.update(member.id for member in group.users)
    return ids


class ZpodPermissionService(ServiceBase):
    base_model: SQLModel = M.ZpodComponent

    def user_add(
        self,
        *,
        zpod: M.Zpod,
        permission: ZpodPermission,
        user: M.User,
    ):
        # Remove user from all permissions
        for perm in zpod.permissions:
            for perm_user in perm.users:
                if perm_user.id == user.id:
                    perm.users.remove(perm_user)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in zpod.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.ZpodPermission(
                permission=permission.value,
                zpod_id=zpod.id,
            )

        # Add user to permission
        perm.users.append(user)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def user_remove(
        self,
        *,
        zpod: M.Zpod,
        permission: ZpodPermission,
        user: M.User,
    ):
        if perm := next(
            (x for x in zpod.permissions if x.permission == permission), None
        ):
            if not any(perm_user.id == user.id for perm_user in perm.users):
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"User not found in permission: {permission}",
                )
            # Refuse to orphan the zPod: a removal must leave at least one
            # owner/admin principal behind.
            if permission in _MAINTAINER_LEVELS and not _remaining_maintainer_user_ids(
                zpod, excluding_user_id=user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot remove the last owner/admin of a zPod",
                )
            for perm_user in perm.users:
                if perm_user.id == user.id:
                    perm.users.remove(perm_user)
                    break
            if not perm.users and not perm.permission_groups:
                self.session.delete(perm)
            self.session.commit()

    def group_add(
        self,
        *,
        zpod: M.Zpod,
        permission: ZpodPermission,
        group: M.PermissionGroup,
    ):
        # Remove group from all permissions
        for perm in zpod.permissions:
            for perm_group in perm.permission_groups:
                if perm_group.id == group.id:
                    perm.permission_groups.remove(perm_group)
                    # Remove permission if no users or groups
                    if not perm.users and not perm.permission_groups:
                        self.session.delete(perm)

        # Find permission record or create one
        for perm in zpod.permissions:
            if perm.permission == permission:
                break
        else:
            perm = M.ZpodPermission(
                permission=permission.value,
                zpod_id=zpod.id,
            )

        # Add group to permission
        perm.permission_groups.append(group)
        self.session.add(perm)
        self.session.commit()
        return perm.users

    def group_remove(
        self,
        *,
        zpod: M.Zpod,
        permission: ZpodPermission,
        group: M.PermissionGroup,
    ):
        if perm := next(
            (x for x in zpod.permissions if x.permission == permission), None
        ):
            if not any(
                perm_group.id == group.id for perm_group in perm.permission_groups
            ):
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"Group not found in permission: {permission}",
                )
            # Refuse to orphan the zPod: a removal must leave at least one
            # owner/admin principal behind.
            if permission in _MAINTAINER_LEVELS and not _remaining_maintainer_user_ids(
                zpod, excluding_group_id=group.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot remove the last owner/admin of a zPod",
                )
            for perm_group in perm.permission_groups:
                if perm_group.id == group.id:
                    perm.permission_groups.remove(perm_group)
                    break
            if not perm.users and not perm.permission_groups:
                self.session.delete(perm)
            self.session.commit()
