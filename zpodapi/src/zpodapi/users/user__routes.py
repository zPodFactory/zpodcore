import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .user__dependencies import UserAnnotations, UserDepends
from .user__schemas import UserCreate, UserUpdate, UserViewFull

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[UserViewFull],
    dependencies=[GlobalDepends.SuperAdminOnly],
)
def get_all(
    *,
    user_service: UserAnnotations.UserService,
    username: str | None = None,
    email: EmailStr | None = None,
):
    return user_service.get_all_filtered(username=username, email=email)


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
    dependencies=[UserDepends.SuperAdminOrActiveUserOnly],
)
def get(
    *,
    user: UserAnnotations.GetUser,
):
    return user


@router.post(
    "",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.SuperAdminOnly],
)
def create(
    *,
    user_service: UserAnnotations.UserService,
    user_in: UserCreate,
):
    if user_service.get_all_filtered(
        username=user_in.username,
        email=user_in.email,
        use_or=True,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return user_service.create(item_in=user_in)


@router.patch(
    "/{id}",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[UserDepends.SuperAdminOrActiveUserOnly],
)
def update(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
    user_in: UserUpdate,
):
    return user_service.update(item=user, item_in=user_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.SuperAdminOnly],
)
def delete(
    *,
    user_service: UserAnnotations.UserService,
    user: UserAnnotations.GetUser,
):
    return user_service.delete(item=user)
