from fastapi import APIRouter, HTTPException, status

from zpodapi.lib import dependencies
from zpodapi.lib.route_logger import RouteLogger
from zpodapi.libraries.library__services import LibraryService

from . import library__dependencies
from .library__schemas import LibraryCreate, LibraryUpdate, LibraryView

router = APIRouter(
    prefix="/libraries",
    tags=["libraries"],
    dependencies=[dependencies.GetCurrentUserAndUpdateDepends],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[LibraryView],
)
def get_all(
    *,
    session: dependencies.GetSession,
):
    return LibraryService(session=session).get_all()


@router.post(
    "",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: dependencies.GetSession,
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
    session: dependencies.GetSession,
    library: library__dependencies.GetLibraryRecord,
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
    session: dependencies.GetSession,
    library: library__dependencies.GetLibraryRecord,
):
    return LibraryService(session=session).delete(item=library)
