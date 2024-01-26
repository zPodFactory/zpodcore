from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import service_init_annotation
from zpodapi.lib.id_types import IdNameType
from zpodcommon import models as M

from .library__services import LibraryService


async def get_library(
    *,
    library_service: "LibraryAnnotations.LibraryService",
    id: Annotated[
        IdNameType,
        Path(
            openapi_examples={
                "id": {"value": "1"},
                "name": {"value": "name=main"},
            },
        ),
    ],
):
    if library := library_service.crud.get(**id):
        return library
    raise HTTPException(status_code=404, detail="Library not found")


class LibraryDepends:
    pass


class LibraryAnnotations:
    GetLibrary = Annotated[M.Library, Depends(get_library)]
    LibraryService = service_init_annotation(LibraryService)
