from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, or_, select

from zpodapi import schemas as S
from zpodapi.lib import deps
from zpodcommon import models as M

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(deps.get_current_user_and_update)],
)


async def get_user_record(
    *,
    session: Session = Depends(deps.get_session),
    username: str | None = None,
    email: str | None = None,
):
    try:
        return session.exec(
            select(M.User).where(
                or_(
                    M.User.username == username,
                    M.User.email == email,
                )
            )
        ).one()
    except (NoResultFound, MultipleResultsFound) as e:
        raise HTTPException(status_code=404, detail="User not found") from e


@router.get(
    "/users",
    response_model=list[S.UserView],
)
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return session.exec(select(M.User)).all()


@router.get(
    "/user/me",
    response_model=S.UserView,
)
def get_me(
    *,
    current_user: M.User = Depends(deps.get_current_user_and_update),
):
    return current_user


@router.get(
    "/user",
    response_model=S.UserView,
)
def get(
    *,
    db_user: M.User = Depends(get_user_record),
):
    return db_user


@router.post(
    "/user",
    response_model=S.UserView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(deps.get_session),
    user: S.UserCreate,
):
    if session.exec(
        select(M.User).where(
            or_(
                M.User.username == user.username,
                M.User.email == user.email,
            )
        )
    ).first():
        raise HTTPException(status_code=422, detail="Conflicting record found")

    db_user = M.User(**user.dict(), creation_date=datetime.now())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.patch(
    "/user",
    response_model=S.UserView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    db_user: M.User = Depends(get_user_record),
    user: S.UserUpdate,
):
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete(
    "/user",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(deps.get_session),
    db_user: M.User = Depends(get_user_record),
):
    session.delete(db_user)
    session.commit()
    return None
