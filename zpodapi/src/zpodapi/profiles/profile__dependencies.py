from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodcommon import models as M

from .profile__services import ProfileService
from .profile__types import ProfileIdType


def get_profile(
    *,
    profile_service: "ProfileAnnotations.ProfileService",
    id: Annotated[
        ProfileIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "sddc"},
            },
        ),
    ],
):
    if profile := profile_service.crud.get(**ProfileIdType.args(id)):
        return profile
    raise HTTPException(status_code=404, detail="Profile not found")


class ProfileDepends:
    pass


class ProfileAnnotations:
    GetProfile = Annotated[M.Profile, Depends(get_profile)]
    ProfileService = service_init_annotation(ProfileService)
