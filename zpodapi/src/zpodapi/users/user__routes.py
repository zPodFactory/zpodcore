import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger

from . import user__dependencies
from .user__schemas import UserCreate, UserUpdate, UserViewFull
from .user__services import UserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[dependencies.GetCurrentUserAndUpdateDepends],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[UserViewFull],
)
def get_all(
    *,
    session: dependencies.GetSession,
    username: str | None = None,
    email: EmailStr | None = None,
):
    return UserService(session=session).get_all_filtered(username=username, email=email)


@router.get(
    "/me",
    response_model=UserViewFull,
)
def get_me(
    *,
    current_user: dependencies.GetCurrentUser,
):
    return current_user


@router.get(
    "/{id}",
    response_model=UserViewFull,
)
def get(
    *,
    user: user__dependencies.GetUserRecord,
):
    return user


@router.post(
    "",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: dependencies.GetSession,
    user_in: UserCreate,
):
    service = UserService(session=session)
    if service.get_all_filtered(
        username=user_in.username,
        email=user_in.email,
        use_or=True,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return service.create(item_in=user_in)


@router.patch(
    "/{id}",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: dependencies.GetSession,
    user: user__dependencies.GetUserRecord,
    user_in: UserUpdate,
):
    return UserService(session=session).update(item=user, item_in=user_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: dependencies.GetSession,
    user: user__dependencies.GetUserRecord,
):
    return UserService(session=session).delete(item=user)
