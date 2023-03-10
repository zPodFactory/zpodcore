from datetime import datetime

from sqlmodel import Session, or_, select

from zpodcommon import models as M

from . import instance_utils
from .instance_schemas import InstanceCreate


def get_all(
    session: Session,
    name: str | None = None,
):
    sel = select(M.Instance)
    or_criteria = []
    if name:
        or_criteria.append(M.Instance.name == name)
    if or_criteria:
        sel = sel.where(or_(*or_criteria))
    return session.exec(sel).all()


def get(
    session: Session,
    *,
    id: int,
):
    instance = session.exec(select(M.Instance).where(M.Instance.id == id)).first()
    print(instance)
    return instance


def create(
    session: Session,
    *,
    current_user: M.User,
    instance_in: InstanceCreate,
):
    now = datetime.now()
    user = M.Instance(
        **instance_in.dict(),
        creation_date=now,
        last_modified_date=now,
        password=instance_utils.gen_password(),
        permissions=[
            M.InstancePermission(
                name="Owner",
                permission="zpodadmin",
                users=[current_user],
            )
        ],
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


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
