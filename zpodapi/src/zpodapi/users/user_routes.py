from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlmodel import Session

from zpodcommon import models as M

from ..lib import dependencies
from . import user_dependencies, user_services
from .user_schemas import UserCreate, UserUpdate, UserView

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
)


@router.get(
    "/users",
    response_model=list[UserView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
    username: str | None = None,
    email: EmailStr | None = None,
):
    return user_services.get_all(session, username=username, email=email)


@router.get(
    "/users/me",
    response_model=UserView,
)
def get_me(
    *,
    current_user: M.User = Depends(dependencies.get_current_user_and_update),
):
    return current_user


@router.get(
    "/users/{id}",
    response_model=UserView,
)
def get(
    *,
    user: M.User = Depends(user_dependencies.get_user_record),
):
    return user


@router.post(
    "/users",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
    user_in: UserCreate,
):
    if user_services.get_all(
        session=session,
        username=user_in.username,
        email=user_in.email,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return user_services.create(session=session, user_in=user_in)


@router.patch(
    "/users/{id}",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    user: M.User = Depends(user_dependencies.get_user_record),
    user_in: UserUpdate,
):
    return user_services.update(
        session=session,
        user=user,
        user_in=user_in,
    )


@router.delete(
    "/users/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    user: M.User = Depends(user_dependencies.get_user_record),
):
    return user_services.delete(session=session, user=user)
