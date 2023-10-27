import secrets

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodapi.users.user__schemas import UserUpdate, UserUpdateAdmin
from zpodcommon import models as M
from zpodcommon.enums import UserStatus

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
