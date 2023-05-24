from pydantic import EmailStr
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodapi.users.user__schemas import UserUpdate, UserUpdateAdmin
from zpodcommon import models as M


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def get_all(self):
        return self.crud.get_all_filtered(
            id=None if self.is_superadmin else self.current_user.id,
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
