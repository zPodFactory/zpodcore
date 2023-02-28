from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import deps
from zpodcommon import models as M

from . import dependencies, services
from .schemas import UserCreate, UserUpdate, UserView

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(deps.get_current_user_and_update)],
)


@router.get("/users", response_model=list[UserView])
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return services.get_all(session)


@router.get("/user/me", response_model=UserView)
def get_me(
    *,
    current_user: M.User = Depends(deps.get_current_user_and_update),
):
    return current_user


@router.get("/user", response_model=UserView)
def get(
    *,
    db_user: M.User = Depends(dependencies.get_user_record),
):
    return db_user


@router.post("/user", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create(
    *,
    session: Session = Depends(deps.get_session),
    user_in: UserCreate,
):
    if services.get(session=session, username=user_in.username, email=user_in.email):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return services.create(session=session, user_in=user_in)


@router.patch(
    "/user",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    user: M.User = Depends(dependencies.get_user_record),
    user_in: UserUpdate,
):
    return services.update(session=session, user=user, user_in=user_in)


@router.delete(
    "/user",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(deps.get_session),
    user: M.User = Depends(dependencies.get_user_record),
):
    return services.delete(session=session, user=user)
