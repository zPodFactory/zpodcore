import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodcommon import models as M

from . import user__dependencies
from .user__schemas import UserCreate, UserUpdate, UserViewFull
from .user__services import UserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[UserViewFull],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
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
    current_user: M.User = Depends(dependencies.get_current_user_and_update),
):
    return current_user


@router.get(
    "/{id}",
    response_model=UserViewFull,
)
def get(
    *,
    user: M.User = Depends(user__dependencies.get_user_record),
):
    return user


@router.post(
    "",
    response_model=UserViewFull,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
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
    session: Session = Depends(dependencies.get_session),
    user: M.User = Depends(user__dependencies.get_user_record),
    user_in: UserUpdate,
):
    return UserService(session=session).update(item=user, item_in=user_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    user: M.User = Depends(user__dependencies.get_user_record),
):
    return UserService(session=session).delete(item=user)
