from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger
from zpodapi.libraries.library__services import LibraryService

from .library__dependencies import LibraryAnnotations
from .library__schemas import LibraryCreate, LibraryUpdate, LibraryView

router = APIRouter(
    prefix="/libraries",
    tags=["libraries"],
    dependencies=[GlobalDepends.UpdateLastConnectionDate],
    route_class=RouteLogger,
)


@router.get(
    "",
    response_model=list[LibraryView],
)
def get_all(
    *,
    session: GlobalAnnotations.GetSession,
):
    return LibraryService(session=session).get_all()


@router.get("/{id}", response_model=LibraryView)
def get(
    *,
    library: LibraryAnnotations.GetLibrary,
):
    return library


@router.post(
    "",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: GlobalAnnotations.GetSession,
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
    "/{id}",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: GlobalAnnotations.GetSession,
    library: LibraryAnnotations.GetLibrary,
    library_in: LibraryUpdate,
):
    return LibraryService(session=session).update(
        item=library,
        item_in=library_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: GlobalAnnotations.GetSession,
    library: LibraryAnnotations.GetLibrary,
):
    return LibraryService(session=session).delete(item=library)
