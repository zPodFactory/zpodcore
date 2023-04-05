from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

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
    library_service: LibraryAnnotations.LibraryService,
):
    return library_service.get_all()


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
    library_service: LibraryAnnotations.LibraryService,
    library_in: LibraryCreate,
):
    if library_service.get_all_filtered(
        name=library_in.name,
        git_url=library_in.git_url,
        use_or=True,
    ):
        raise HTTPException(status_code=422, detail="Conflicting record found")
    return library_service.create(item_in=library_in)


@router.patch(
    "/{id}",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    library_service: LibraryAnnotations.LibraryService,
    library: LibraryAnnotations.GetLibrary,
    library_in: LibraryUpdate,
):
    return library_service.update(
        item=library,
        item_in=library_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    library_service: LibraryAnnotations.LibraryService,
    library: LibraryAnnotations.GetLibrary,
):
    return library_service.delete(item=library)
