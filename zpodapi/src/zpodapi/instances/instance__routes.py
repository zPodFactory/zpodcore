from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodapi.lib.route_logger import RouteLogger

from .instance__dependencies import InstanceAnnotations
from .instance__schemas import InstanceCreate, InstanceUpdate, InstanceView

router = APIRouter(
    prefix="/instances",
    tags=["instances"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[InstanceView],
    response_model_exclude_unset=True,
)
def get_all(
    *,
    instance_service: InstanceAnnotations.InstanceService,
):
    return instance_service.get_all()


@router.get(
    "/{id}",
    response_model=InstanceView,
    response_model_exclude_unset=True,
)
def get(
    *,
    instance: InstanceAnnotations.GetInstance,
):
    return instance


# TODO: ADD User Permissions to prevent creation
@router.post(
    "",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_unset=True,
)
def create(
    *,
    instance_service: InstanceAnnotations.InstanceService,
    current_user: GlobalAnnotations.GetCurrentUser,
    instance_in: InstanceCreate,
):
    if instance_service.get(name=instance_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )
    return instance_service.create(current_user=current_user, item_in=instance_in)


@router.patch(
    "/{id}",
    response_model=InstanceView,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_unset=True,
)
def update(
    *,
    instance_service: InstanceAnnotations.InstanceService,
    instance: InstanceAnnotations.GetInstance,
    instance_in: InstanceUpdate,
):
    return instance_service.crud.update(
        item=instance,
        item_in=instance_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    instance_service: InstanceAnnotations.InstanceService,
    instance: InstanceAnnotations.GetInstance,
):
    return instance_service.delete(instance=instance)
