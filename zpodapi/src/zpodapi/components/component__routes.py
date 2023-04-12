from fastapi import APIRouter, status
from zpodapi.lib.global_dependencies import GlobalDepends

from zpodapi.lib.route_logger import RouteLogger

from .component__dependencies import ComponentAnnotations
from .component__schemas import ComponentViewFull

router = APIRouter(
    prefix="/components",
    tags=["components"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ComponentViewFull],
)
def get_all(
    *,
    component_service: ComponentAnnotations.ComponentService,
):
    return component_service.crud.get_all()


@router.get(
    "/{id}",
    response_model=ComponentViewFull,
)
def get(
    *,
    component: ComponentAnnotations.GetComponent,
):
    return component


@router.put(
    "/{id}/enable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def enable(
    *,
    component_service: ComponentAnnotations.ComponentService,
    component: ComponentAnnotations.GetComponent,
):
    return component_service.enable(component=component)


@router.put(
    "/{id}/disable",
    response_model=ComponentViewFull,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def disable(
    *,
    component_service: ComponentAnnotations.ComponentService,
    component: ComponentAnnotations.GetComponent,
):
    return component_service.disable(component=component)
