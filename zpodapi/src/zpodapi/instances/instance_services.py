from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Session, or_, select

from zpodcommon import models as M

# from .user_schemas import UserCreate, UserUpdate
# from .user_types import UserIdType


def get_all(
    session: Session,
):
    sel = select(M.Instance)
    return session.exec(sel).all()


# def get(
#     session: Session,
#     *,
#     id: UserIdType,
# ):
#     idtype, id_ = (id if "=" in id else f"id={id}").split("=")
#     criteria = getattr(M.User, idtype) == id_
#     return session.exec(select(M.User).where(criteria)).first()


# def create(session: Session, *, user_in: UserCreate):
#     user = M.User(**user_in.dict(), creation_date=datetime.now())
#     session.add(user)
#     session.commit()
#     session.refresh(user)
#     return user


# def update(session: Session, *, user: M.User, user_in: UserUpdate):
#     data = user_in.dict(exclude_unset=True)
#     data.pop("id", None)
#     for key, value in data.items():
#         setattr(user, key, value)

#     session.add(user)
#     session.commit()
#     session.refresh(user)
#     return user


# def delete(session: Session, *, user: M.User):
#     session.delete(user)
#     session.commit()
#     return None
