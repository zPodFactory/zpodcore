import os

from sqlmodel import Session, select

from zpodcommon import models as M
from zpodcommon.lib import zpodengine

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
    filename: str,
):
    component_enabled = component_in.enabled is True and component.enabled is False
    for key, value in component_in.dict(exclude_unset=True).items():
        setattr(component, key, value)

    session.add(component)
    session.commit()
    session.refresh(component)

    if component_enabled:
        zpod_engine = zpodengine.ZpodEngine()
        vcc_username = os.getenv("ZPODENGINE_VCC_USER")
        vcc_password = os.getenv("ZPODENGINE_VCC_PASS")
        vcc_request = zpodengine.read_json_file(
            filename=filename.split("/")[-1],
            filepath="/library",
        )
        print(vcc_request["component_download_file"])
        zpod_engine.create_flow_run_by_name(
            flow_name="download-component",
            deployment_name="component",
            vcc_username=vcc_username,
            vcc_password=vcc_password,
            zpod_path="/products",
            vcc_request=vcc_request,
            component_download_file=vcc_request["component_download_file"],
        )

    return component
