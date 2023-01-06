from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, or_, select

from zpodapi.lib import deps
from zpodapi.models import User, UserCreate, UserUpdate, UserView

router = APIRouter(
    tags=["users"],
    dependencies=[Depends(deps.get_active_current_user)],
)


async def get_user_record(
    *,
    session: Session = Depends(deps.get_session),
    username: str | None = None,
    email: str | None = None,
):
    try:
        return session.exec(
            select(User).where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        ).one()
    except (NoResultFound, MultipleResultsFound) as e:
        raise HTTPException(status_code=404, detail="User not found") from e


@router.get(
    "/users",
    response_model=list[UserView],
)
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return session.exec(select(User)).all()


@router.get(
    "/user",
    response_model=UserView,
)
def get(
    *,
    db_user: User = Depends(get_user_record),
):
    return db_user


@router.post(
    "/user",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(deps.get_session),
    user: UserCreate,
):
    if session.exec(
        select(User).where(
            or_(
                User.username == user.username,
                User.email == user.email,
            )
        )
    ).first():
        raise HTTPException(status_code=422, detail="Conflicting record found")

    db_user = User(**user.dict(), creation_date=datetime.now())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.patch(
    "/user",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    db_user: User = Depends(get_user_record),
    user: UserUpdate,
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
    db_user: User = Depends(get_user_record),
):
    session.delete(db_user)
    session.commit()
    return None
