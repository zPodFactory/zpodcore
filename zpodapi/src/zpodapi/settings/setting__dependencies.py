from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.settings.setting__types import SettingIdType
from zpodcommon import models as M

from .setting__services import SettingService


async def get_setting(
    *,
    setting_service: "SettingAnnotations.SettingService",
    id: Annotated[
        SettingIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "name=main"},
            },
        ),
    ],
):
    if setting := setting_service.crud.get(**SettingIdType.args(id)):
        return setting
    raise HTTPException(status_code=404, detail="Setting not found")


class SettingDepends:
    pass


class SettingAnnotations:
    GetSetting = Annotated[M.Setting, Depends(get_setting)]
    SettingService = service_init_annotation(SettingService)
