from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodapi.libraries.library__services import LibraryService
from zpodcommon import models as M

from . import library__dependencies
from .library__schemas import LibraryCreate, LibraryUpdate, LibraryView

router = APIRouter(
    prefix="/libraries",
    tags=["libraries"],
    dependencies=[Depends(dependencies.get_current_user_and_update)],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[LibraryView],
)
def get_all(
    *,
    session: Session = Depends(dependencies.get_session),
):
    return LibraryService(session=session).get_all()


@router.post(
    "",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(dependencies.get_session),
    library_in: LibraryCreate,
):
    service = LibraryService(session=session)
    if service.get_all_filtered(
        name=library_in.name,
        git_url=library_in.git_url,
        use_or=True,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return service.create(item_in=library_in)


@router.patch(
    "",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    library: M.Library = Depends(library__dependencies.get_library_record),
    library_in: LibraryUpdate,
):
    return LibraryService(session=session).update(
        item=library,
        item_in=library_in,
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    library: M.Library = Depends(library__dependencies.get_library_record),
):
    return LibraryService(session=session).delete(item=library)
