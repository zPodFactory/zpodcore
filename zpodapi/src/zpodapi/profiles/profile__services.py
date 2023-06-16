from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .profile__utils import validate_profile


class ProfileService(ServiceBase):
    base_model: SQLModel = M.Profile

    def get(
        self,
        id: int | None = None,
        name: str | None = None,
        name_insensitive: str | None = None,
    ):
        return self.crud.get(
            id=id,
            name=name,
            name_insensitive=name_insensitive,
        )

    def validate_profile(self, profile_obj):
        validate_profile(session=self.session, profile_obj=profile_obj)
