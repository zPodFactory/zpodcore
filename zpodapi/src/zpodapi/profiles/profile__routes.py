from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .profile__dependencies import ProfileAnnotations
from .profile__schemas import ProfileCreate, ProfileUpdate, ProfileView

router = APIRouter(
    prefix="/profiles",
    tags=["profiles"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ProfileView],
    response_model_exclude_none=True,
)
def get_all(
    *,
    profile_service: ProfileAnnotations.ProfileService,
):
    return profile_service.crud.get_all()


@router.get(
    "/{id}",
    response_model=ProfileView,
    response_model_exclude_none=True,
)
def get(
    *,
    profile: ProfileAnnotations.GetProfile,
):
    return profile


@router.post(
    "",
    response_model=ProfileView,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    *,
    profile_service: ProfileAnnotations.ProfileService,
    profile_in: ProfileCreate,
    force=False,
):
    if profile_service.crud.get_all_filtered(name=profile_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists",
        )
    if not force:
        profile_service.validate_profile(profile_obj=profile_in.model_dump()["profile"])
    return profile_service.crud.create(item_in=profile_in)


@router.patch(
    "/{id}",
    response_model=ProfileView,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def update(
    *,
    profile_service: ProfileAnnotations.ProfileService,
    profile: ProfileAnnotations.GetProfile,
    profile_in: ProfileUpdate,
):
    if profile_in.name and profile_service.crud.get_all_filtered(name=profile_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )

    if profile_in.profile:
        profile_service.validate_profile(profile_obj=profile_in.model_dump()["profile"])

    return profile_service.crud.update(item=profile, item_in=profile_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def delete(
    *,
    profile_service: ProfileAnnotations.ProfileService,
    profile: ProfileAnnotations.GetProfile,
):
    return profile_service.crud.delete(item=profile)
