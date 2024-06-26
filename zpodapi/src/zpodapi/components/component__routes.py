from fastapi import APIRouter, Form, UploadFile, status
from fastapi.responses import JSONResponse

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger
from zpodapi.lib.types import FILENAME

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


@router.post(
    "/upload",
    operation_id="components_upload",
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
async def upload(
    component_service: ComponentAnnotations.ComponentService,
    file: UploadFile,
    filename: FILENAME = Form(...),
    offset: int = Form(...),
    file_size: int = Form(...),
):
    current_size = await component_service.upload(
        file=file,
        filename=filename,
        offset=offset,
        file_size=file_size,
    )
    return JSONResponse({"filename": filename, "current_size": current_size})


@router.get(
    "/upload/{filename}",
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
async def upload_filesize(
    component_service: ComponentAnnotations.ComponentService,
    filename: FILENAME,
):
    current_size = await component_service.upload_filesize(filename=filename)
    return JSONResponse({"filename": filename, "current_size": current_size})
