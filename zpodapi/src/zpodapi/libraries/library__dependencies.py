from typing import Annotated

from fastapi import Depends, HTTPException

from zpodapi.lib.global_dependencies import GlobalAnnotations
from zpodcommon import models as M

from .library__services import LibraryService


async def get_library(
    *,
    session: GlobalAnnotations.GetSession,
    name: str | None = None,
):
    if library := LibraryService(session=session).get(value=name):
        return library
    raise HTTPException(status_code=404, detail="Library not found")


class LibraryDepends:
    GetLibrary = Depends(get_library)


class LibraryAnnotations:
    GetLibrary = Annotated[M.Library, LibraryDepends.GetLibrary]
