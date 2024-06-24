import os

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
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
    file: UploadFile,
    filename: FILENAME = Form(...),
    offset: int = Form(...),
):
    file_location = os.path.join("/products", filename)

    # Check if the file exists and handle accordingly
    if os.path.exists(file_location):
        current_size = os.path.getsize(file_location)
        if offset != current_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset does not match the current file size.",
            )
    elif offset != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not exist, offset must be 0.",
        )

    with open(file_location, "ab") as f:
        f.seek(offset)
        f.write(await file.read())

    current_size = os.path.getsize(file_location)
    return JSONResponse({"filename": filename, "current_size": current_size})


@router.get(
    "/upload/{filename}",
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
async def upload_filesize(filename: FILENAME):
    file_location = os.path.join("/products", filename)
    if os.path.exists(file_location):
        current_size = os.path.getsize(file_location)
        return JSONResponse({"filename": filename, "current_size": current_size})
    else:
        return JSONResponse({"filename": filename, "current_size": 0})


@router.post("/sync/{filename}", dependencies=[GlobalDepends.OnlySuperAdmin])
async def sync(
    filename: FILENAME,
    component_service: ComponentAnnotations.ComponentService,
):
    #
    # File has been uploaded, now we need to checksum it and enable the component

    return component_service.sync(filename=filename)
