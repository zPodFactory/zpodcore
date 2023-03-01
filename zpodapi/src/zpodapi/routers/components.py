import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, or_, select

from zpodapi import schemas as S
from zpodapi.lib import deps
from zpodcommon import models as M
from zpodcommon.lib import zpodengine

router = APIRouter(
    tags=["components"],
    dependencies=[Depends(deps.get_current_user_and_update)],
)


async def get_component_record(
    *, session: Session = Depends(deps.get_session), filename: str | None = None
):
    try:
        return session.exec(
            select(M.Component).where(or_(M.Component.filename == filename))
        ).one()
    except (NoResultFound, MultipleResultsFound) as e:
        raise HTTPException(status_code=404, detail="Component not found") from e


@router.get(
    "/components",
    response_model=list[S.ComponentView],
)
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return session.exec(select(M.Component)).all()


@router.patch(
    "/components",
    response_model=S.ComponentView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    db_component: M.Component = Depends(get_component_record),
    component: S.ComponentUpdate,
    component_uid: str = Query(),
):
    component_enabled = component.enabled is True and db_component.enabled is False

    for key, value in component.dict(exclude_unset=True).items():
        setattr(db_component, key, value)

    session.add(db_component)
    session.commit()
    session.refresh(db_component)

    if component_enabled:
        zpod_engine = zpodengine.ZpodEngine()
        zpod_engine.create_flow_run_by_name(
            flow_name="download-component",
            deployment_name="component",
            component_uid=component_uid,
        )
    return db_component
