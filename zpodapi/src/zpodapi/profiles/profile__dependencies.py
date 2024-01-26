from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.id_types import IdNameType
from zpodcommon import models as M

from .profile__services import ProfileService


def get_profile(
    *,
    profile_service: "ProfileAnnotations.ProfileService",
    id: Annotated[
        IdNameType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "name": {"value": "sddc"},
            },
        ),
    ],
):
    if profile := profile_service.crud.get(**id):
        return profile
    raise HTTPException(status_code=404, detail="Profile not found")


class ProfileDepends:
    pass


class ProfileAnnotations:
    GetProfile = Annotated[M.Profile, Depends(get_profile)]
    ProfileService = service_init_annotation(ProfileService)
