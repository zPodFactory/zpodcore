from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .setting__dependencies import SettingAnnotations
from .setting__schemas import SettingCreate, SettingUpdate, SettingView

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[SettingView],
)
def get_all(
    *,
    setting_service: SettingAnnotations.SettingService,
):
    return setting_service.crud.get_all()


@router.get("/{id}", response_model=SettingView)
def get(
    *,
    setting: SettingAnnotations.GetSetting,
):
    return setting


@router.post(
    "",
    response_model=SettingView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    *,
    setting_service: SettingAnnotations.SettingService,
    setting_in: SettingCreate,
):
    if setting_service.crud.get_all_filtered(name=setting_in.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting record found",
        )
    return setting_service.create(item_in=setting_in)


@router.patch(
    "/{id}",
    response_model=SettingView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def update(
    *,
    setting_service: SettingAnnotations.SettingService,
    setting: SettingAnnotations.GetSetting,
    setting_in: SettingUpdate,
):
    return setting_service.crud.update(
        item=setting,
        item_in=setting_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def delete(
    *,
    setting_service: SettingAnnotations.SettingService,
    setting: SettingAnnotations.GetSetting,
):
    return setting_service.delete(item=setting)
