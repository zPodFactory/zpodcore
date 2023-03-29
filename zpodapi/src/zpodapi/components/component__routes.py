from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .component__dependencies import ComponentAnnotations
from .component__schemas import ComponentViewFull
from .component__services import ComponentService

router = APIRouter(
    prefix="/components",
    tags=["components"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ComponentViewFull],
)
def get_all(
    *,
    session: GlobalAnnotations.GetSession,
):
    return ComponentService(session=session).get_all()


@router.get(
    "/{component_uid}",
    response_model=ComponentViewFull,
)
def get(
    *,
    component: ComponentAnnotations.GetComponent,
):
    return component


@router.put(
    "/{component_uid}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def enable(
    *,
    session: GlobalAnnotations.GetSession,
    component: ComponentAnnotations.GetComponent,
):
    return ComponentService(session=session).enable(component=component)


@router.put(
    "/{component_uid}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
)
def disable(
    *,
    session: GlobalAnnotations.GetSession,
    component: ComponentAnnotations.GetComponent,
):
    return ComponentService(session=session).disable(component=component)
