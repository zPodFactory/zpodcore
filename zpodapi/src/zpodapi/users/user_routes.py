from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlmodel import Session, or_

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodcommon import models as M

from . import user_dependencies
from .user_schemas import UserCreate, UserUpdate, UserViewFull
from .user_services import UserService

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
    return UserService(session=session).get_all(
        criteria=(
            M.User.username == username,
            M.User.email == email,
        )
    )


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
    user: M.User = Depends(user_dependencies.get_user_record),
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
    if service.get_all(
        criteria=(
            or_(
                M.User.username == user_in.username,
                M.User.email == user_in.email,
            )
        )
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
    user: M.User = Depends(user_dependencies.get_user_record),
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
    user: M.User = Depends(user_dependencies.get_user_record),
):
    return UserService(session=session).delete(item=user)
