from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Session, or_, select

from zpodcommon import models as M

from .user_schemas import UserCreate, UserUpdate


def get_all(session: Session):
    return session.exec(select(M.User)).all()


def get(
    session: Session,
    *,
    username: str | None = None,
    email: EmailStr | None = None,
):
    return session.exec(
        select(M.User).where(
            or_(
                M.User.username == username,
                M.User.email == email,
            )
        )
    ).first()


def create(session: Session, *, user_in: UserCreate):
    user = M.User(**user_in.dict(), creation_date=datetime.now())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update(session: Session, *, user: M.User, user_in: UserUpdate):
    for key, value in user_in.dict(exclude_unset=True).items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete(session: Session, *, user: M.User):
    session.delete(user)
    session.commit()
    return None
