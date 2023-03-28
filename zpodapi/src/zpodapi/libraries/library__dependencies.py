from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodcommon import models as M

from .library__services import LibraryService


async def get_library_record(
    *,
    session: Session = Depends(dependencies.get_session),
    name: str | None = None,
):
    if library := LibraryService(session=session).get(value=name):
        return library
    raise HTTPException(status_code=404, detail="Library not found")


GetLibraryRecordDepends = Depends(get_library_record)
GetLibraryRecord = Annotated[M.Library, GetLibraryRecordDepends]
