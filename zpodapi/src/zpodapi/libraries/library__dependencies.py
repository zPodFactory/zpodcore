from typing import Annotated

from fastapi import Depends, HTTPException, Path

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodapi.libraries.library__types import LibraryIdType
from zpodcommon import models as M

from .library__services import LibraryService


async def get_library(
    *,
    session: GlobalAnnotations.GetSession,
    id: Annotated[
        LibraryIdType,
        Path(
            examples={
                "id": {"value": "1"},
                "name": {"value": "name=main"},
            },
        ),
    ],
):
    if library := LibraryService(session=session).get(value=id):
        return library
    raise HTTPException(status_code=404, detail="Library not found")


class LibraryDepends:
    GetLibrary = Depends(get_library)


class LibraryAnnotations:
    GetLibrary = Annotated[M.Library, LibraryDepends.GetLibrary]
