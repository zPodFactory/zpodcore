import secrets

from pydantic import EmailStr
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodapi.users.user__schemas import UserUpdate, UserUpdateAdmin
from zpodcommon import models as M
from zpodcommon.enums import UserStatus

from .user__schemas import UserUpdateStatus, UserUpdateApiToken


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def create(self, user_in):
        return self.crud.create(
            item_in=user_in,
            extra=dict(
                status=UserStatus.ACTIVE,
                api_token=generate_api_token(),
            ),
        )

    def get_all(self, all: bool = False):
        return self.crud.get_all_filtered(
            id=None if self.is_superadmin else self.current_user.id,
            where_extra=None if all else [M.User.status == UserStatus.ACTIVE],
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

    def activate(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateStatus(
                status=UserStatus.ACTIVE,
            ),
        )

    def inactivate(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateStatus(
                status=UserStatus.INACTIVE,
            ),
        )

    def reset_api_token(self, *, item: M.User):
        return self.crud.update(
            item=item,
            item_in=UserUpdateApiToken(
                api_token=generate_api_token(),
            ),
        )


def generate_api_token():
    return secrets.token_urlsafe(32)
