from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import deps
from zpodcommon import models as M

from . import user_dependencies, user_services
from .user_schemas import UserCreate, UserUpdate, UserView

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(deps.get_current_user_and_update)],
)


@router.get("/users", response_model=list[UserView])
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return user_services.get_all(session)


@router.get("/user/me", response_model=UserView)
def get_me(
    *,
    current_user: M.User = Depends(deps.get_current_user_and_update),
):
    return current_user


@router.get("/user", response_model=UserView)
def get(
    *,
    db_user: M.User = Depends(user_dependencies.get_user_record),
):
    return db_user


@router.post("/user", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create(
    *,
    session: Session = Depends(deps.get_session),
    user_in: UserCreate,
):
    if user_services.get(
        session=session,
        username=user_in.username,
        email=user_in.email,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return user_services.create(session=session, user_in=user_in)


@router.patch(
    "/user",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    user: M.User = Depends(user_dependencies.get_user_record),
    user_in: UserUpdate,
):
    return user_services.update(session=session, user=user, user_in=user_in)


@router.delete(
    "/user",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(deps.get_session),
    user: M.User = Depends(user_dependencies.get_user_record),
):
    return user_services.delete(session=session, user=user)
