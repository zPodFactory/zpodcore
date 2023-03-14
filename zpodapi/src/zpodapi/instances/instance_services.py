from datetime import datetime

from sqlmodel import Session, or_, select

from zpodcommon import models as M

from . import instance_utils
from .instance_schemas import InstanceComponentCreate, InstanceCreate, InstanceUpdate


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


def update(
    session: Session,
    *,
    instance: M.Instance,
    instance_in: InstanceUpdate,
):
    data = instance_in.dict(exclude_unset=True)
    data.pop("id", None)
    for key, value in data.items():
        setattr(instance, key, value)

    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def delete(session: Session, *, instance: M.Instance):
    session.delete(instance)
    session.commit()
    return None


def components_get_all(
    session: Session,
    instance: M.Instance,
):
    return instance.components


def components_create(
    session: Session,
    *,
    instance: M.Instance,
    component_in: InstanceComponentCreate,
):
    instance = M.InstanceComponent(
        instance_id=instance.id,
        component_uid=component_in.component_uid,
    )
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def components_delete(session: Session, *, instance: M.Instance, component_uid: str):
    instance_component = session.exec(
        select(M.InstanceComponent).where(
            M.InstanceComponent.instance_id == instance.id,
            M.InstanceComponent.component_uid == component_uid,
        )
    ).first()

    session.delete(instance_component)
    session.commit()
    return None


def features_get_all(
    session: Session,
    instance: M.Instance,
):
    return instance.features


def networks_get_all(
    session: Session,
    instance: M.Instance,
):
    return instance.networks
