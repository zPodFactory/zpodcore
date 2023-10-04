import logging

from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .user__dependencies import UserAnnotations
from .user__schemas import (
    UserCreate,
    UserUpdate,
    UserUpdateAdmin,
    UserViewFull,
    UserViewFullPlus,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[UserViewFull],
)
def get_all(
    *,
    user_service: UserAnnotations.UserService,
    all: bool = False,
):
    return user_service.get_all(all=all)


@router.get(
    "/me",
    response_model=UserViewFull,
)
def get_me(
    *,
    current_user: GlobalAnnotations.GetCurrentUser,
):
    return current_user


@router.get(
    "/{id}",
    response_model=UserViewFull,
)
def get(
    *,
    user: UserAnnotations.GetUser,
):
    return user


@router.post(
    "",
    response_model=UserViewFullPlus,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    *,
    user_service: UserAnnotations.UserService,
    user_in: UserCreate,
):
    if user_service.crud.get_all_filtered(
        username=user_in.username,
        email=user_in.email,
        use_or=True,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )
    return user_service.create(user_in=user_in)


@router.patch(
    "/{id}",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
    user_in: UserUpdateAdmin | UserUpdate,
):
    return user_service.update(item=user, item_in=user_in)


@router.patch(
    "/{id}/enable",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def enable(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
):
    return user_service.enable(item=user)


@router.patch(
    "/{id}/disable",
    response_model=UserViewFull,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def disable(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
):
    return user_service.disable(item=user)


@router.patch(
    "/{id}/reset_api_token",
    response_model=UserViewFullPlus,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def reset_api_token(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
):
    return user_service.reset_api_token(item=user)
