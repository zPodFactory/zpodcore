from sqlmodel import Session, select

from zpodcommon import models as M
from zpodcommon.lib import zpodengine

from .component__schemas import ComponentUpdate


def get_all(session: Session):
    return session.exec(select(M.Component)).all()


def get(session: Session, *, component_in: ComponentUpdate):
    return session.exec(
        select(M.Component).where(
            M.Component.component_uid == component_in.component_uid,
        )
    ).first()


def enable(
    session: Session,
    *,
    component_in: ComponentUpdate,
):
    component = get(session=session, component_in=component_in)
    component.enabled = True
    component.status = "SCHEDULED"
    session.add(component)
    session.commit()
    session.refresh(component)
    zpod_engine = zpodengine.ZpodEngine()
    zpod_engine.create_flow_run_by_name(
        flow_name="flow-download-component",
        deployment_name="default",
        uid=component.component_uid,
    )
    return component


def disable(
    session: Session,
    *,
    component_in: ComponentUpdate,
):
    component = get(session=session, component_in=component_in)
    component.enabled = False
    session.add(component)
    session.commit()
    session.refresh(component)
    return component
