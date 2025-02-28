from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod__schemas import ZpodCreate, ZpodUpdate, ZpodView

router = APIRouter(
    prefix="/zpods",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[ZpodView],
    response_model_exclude_unset=True,
)
def get_all(
    *,
    zpod_service: ZpodAnnotations.ZpodService,
):
    return zpod_service.get_all()


@router.get(
    "/{id}",
    response_model=ZpodView,
    response_model_exclude_unset=True,
)
def get(
    *,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod


@router.post(
    "",
    response_model=ZpodView,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_unset=True,
)
def create(
    *,
    zpod_service: ZpodAnnotations.ZpodService,
    current_user: GlobalAnnotations.GetCurrentUser,
    zpod_in: ZpodCreate,
):
    if zpod_service.get(name=zpod_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="zPod already exists",
        )

    zpod_service.validate_profile(profile_name=zpod_in.profile)
    return zpod_service.create(
        current_user=current_user,
        item_in=zpod_in,
    )


@router.patch(
    "/{id}",
    response_model=ZpodView,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_unset=True,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def update(
    *,
    zpod_service: ZpodAnnotations.ZpodService,
    zpod: ZpodAnnotations.GetZpod,
    zpod_in: ZpodUpdate,
):
    return zpod_service.crud.update(
        item=zpod,
        item_in=zpod_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def delete(
    *,
    zpod_service: ZpodAnnotations.ZpodService,
    zpod: ZpodAnnotations.GetZpod,
):
    return zpod_service.delete(zpod=zpod)
