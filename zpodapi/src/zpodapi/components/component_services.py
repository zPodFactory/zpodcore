from sqlmodel import Session, select

from zpodcommon import models as M

from .component_schemas import ComponentUpdate


def get_all(session: Session):
    return session.exec(select(M.Component)).all()


def get(
    session: Session,
    *,
    filename: str | None = None,
):
    return session.exec(
        select(M.Component).where(
            M.Component.filename == filename,
        )
    ).first()


def update(
    session: Session,
    *,
    component: M.Component,
    component_in: ComponentUpdate,
):
    becomingEnabled = component_in.enabled is True and component.enabled is False
    for key, value in component_in.dict(exclude_unset=True).items():
        setattr(component, key, value)

    session.add(component)
    session.commit()
    session.refresh(component)

    if becomingEnabled:
        # call zpodengine deployment/flow vcc stuff
        ...

    return component
