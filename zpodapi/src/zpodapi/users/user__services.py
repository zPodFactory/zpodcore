from pydantic import EmailStr
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodapi.users.user__schemas import UserUpdate
from zpodcommon import models as M


class UserService(ServiceBase):
    base_model: SQLModel = M.User

    def get_all(self):
        return self.crud.get_all_filtered(
            id=None if self.current_user.superadmin else self.current_user.id,
        )

    def get(
        self,
        *,
        id: int | None = None,
        username: str | None = None,
        email: EmailStr | None = None,
    ):  # sourcery skip: avoid-builtin-shadow
        if not self.current_user.superadmin:
            if id and int(id) != self.current_user.id:
                return []
            id = self.current_user.id
        return self.crud.get(
            id=id,
            username=username,
            email=email,
        )

    def update(self, *, item: M.User, item_in: UserUpdate):
        return self.crud.update(item=item, item_in=item_in)
