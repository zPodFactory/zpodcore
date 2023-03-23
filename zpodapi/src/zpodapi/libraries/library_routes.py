from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodcommon import models as M

from . import library_dependencies, library_services
from .library_schemas import LibraryCreate, LibraryUpdate, LibraryView

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
    return library_services.get_all(session)


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
    if library_services.get(
        session=session,
        name=library_in.name,
        git_url=library_in.git_url,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return library_services.create(session=session, library_in=library_in)


@router.patch(
    "",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(dependencies.get_session),
    library: M.Library = Depends(library_dependencies.get_library_record),
    library_in: LibraryUpdate,
):
    return library_services.update(
        session=session,
        library=library,
        library_in=library_in,
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(dependencies.get_session),
    library: M.Library = Depends(library_dependencies.get_library_record),
):
    return library_services.delete(session=session, library=library)
