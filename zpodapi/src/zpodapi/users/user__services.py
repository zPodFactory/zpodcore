import secrets

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import SQLModel, select

from zpodapi.lib.service_base import ServiceBase
from zpodapi.users.user__schemas import UserUpdate, UserUpdateAdmin
from zpodcommon import models as M
from zpodcommon.enums import UserStatus, ZpodPermission
from zpodcommon.models import ZpodPermissionUserLink

from .user__schemas import UserUpdateApiToken, UserUpdateStatus


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def create(self, user_in):
        return self.crud.create(
            item_in=user_in,
            extra={
                "status": UserStatus.ENABLED,
                "api_token": generate_api_token(),
            },
        )

    def get_all(self, all: bool = False):
        return self.crud.get_all_filtered(
            id=None if self.is_superadmin else self.current_user.id,
            where_extra=None if all else [M.User.status == UserStatus.ENABLED],
        )

    def get(
        self,
        *,
        id: int | None = None,
        username: str | None = None,
        username_insensitive: str | None = None,
        email: EmailStr | None = None,
        email_insensitive: EmailStr | None = None,
    ):  # sourcery skip: avoid-builtin-shadow
        if not self.is_superadmin:
            if id and int(id) != self.current_user.id:
                return []
            id = self.current_user.id
        return self.crud.get(
            id=id,
            username=username,
            username_insensitive=username_insensitive,
            email=email,
            email_insensitive=email_insensitive,
        )

    def update(self, *, item: M.User, item_in: UserUpdateAdmin | UserUpdate):
        if not self.is_superadmin:
            item_in = self.convert_schema(UserUpdate, item_in)

        return self.crud.update(item=item, item_in=item_in)

    def delete(self, *, item: M.User):
        # Prevent deletion of superuser (id=1)
        if item.id == 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="superuser (id=1) is protected",
            )

        print(
            f"\n=== Starting user deletion process for user {item.username} (id: {item.id}) ==="
        )

        # Find user with id=1 (superuser) to reassign ownership
        superuser = self.session.get(M.User, 1)
        print(f"Found superuser: {superuser.username} (id: {superuser.id})")

        # Get all zpod permissions where this user is an owner
        print("\nSearching for zpod permissions where user is owner...")
        owner_permissions = self.session.exec(
            select(M.ZpodPermission)
            .join(ZpodPermissionUserLink)
            .where(
                ZpodPermissionUserLink.user_id == item.id,
                M.ZpodPermission.permission == ZpodPermission.OWNER,
            )
        ).all()

        print(f"Found {len(owner_permissions)} owner permissions")
        for zpod_permission in owner_permissions:
            print(
                f"\nProcessing zpod permission for zpod_id: {zpod_permission.zpod_id}\n"
                f"- zpod_name: {zpod_permission.zpod.name}"
            )
            print("Before changes:")
            print(f"  - Permission type: {zpod_permission.permission}")
            print(f"  - Current users: {[u.username for u in zpod_permission.users]}")

            # Remove the user from the permission
            for user in zpod_permission.users:
                if user.id == item.id:
                    zpod_permission.users.remove(user)
                    print(f"  - Removed user: {user.username}")

            # Add superuser to the permission
            zpod_permission.users.append(superuser)
            print(f"  - Added superuser: {superuser.username}")
            print("After changes:")
            print(f"  - Final users: {[u.username for u in zpod_permission.users]}")
            self.session.add(zpod_permission)

        # Check group-based zpod permissions as a backup
        print("\nChecking group-based permissions...")
        for group in item.permission_groups:
            print(f"\nProcessing group: {group.name}")
            for zpod_permission in group.zpod_permissions:
                if zpod_permission.permission == "OWNER":
                    print(
                        f"\nFound owner permission in group for zpod_id: {zpod_permission.zpod_id}"
                    )
                    print("Before changes:")
                    print(f"  - Permission type: {zpod_permission.permission}")
                    print(
                        f"  - Current users: {[u.username for u in zpod_permission.users]}"
                    )

                    # Reassign ownership to superuser
                    for user in zpod_permission.users:
                        if user.id == item.id:
                            zpod_permission.users.remove(user)
                            print(f"  - Removed user: {user.username}")

                    zpod_permission.users.append(superuser)
                    print(f"  - Added superuser: {superuser.username}")
                    print("After changes:")
                    print(
                        f"  - Final users: {[u.username for u in zpod_permission.users]}"
                    )
                    self.session.add(zpod_permission)

        # Commit the changes to the database
        print("\nCommitting changes to database...")
        self.session.commit()
        print("Changes committed successfully")

        print(f"\n=== Proceeding with user deletion for {item.username} ===")
        return self.crud.delete(item=item)

    def enable(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateStatus(
                status=UserStatus.ENABLED,
            ),
        )

    def disable(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateStatus(
                status=UserStatus.DISABLED,
            ),
        )

    def reset_api_token(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateApiToken(
                api_token=generate_api_token(),
            ),
        )

    def get_user_record(self, user_id, username):
        if (user_id and username) or (not user_id and not username):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Must provide user_id or username",
            )
        elif user_id and not (user := self.session.get(M.User, user_id)):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found",
            )
        elif username and not (
            user := self.crud.select(where=[M.User.username == username]).one_or_none()
        ):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found",
            )
        return user


def generate_api_token():
    return secrets.token_urlsafe(32)
