from fastapi import APIRouter, HTTPException, status

from zpodapi.lib.global_dependencies import GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .library__dependencies import LibraryAnnotations
from .library__schemas import LibraryCreate, LibraryUpdate, LibraryView

router = APIRouter(
    prefix="/libraries",
    tags=["libraries"],
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
    return library_service.crud.get_all()


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
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def create(
    *,
    library_service: LibraryAnnotations.LibraryService,
    library_in: LibraryCreate,
):
    if library_service.crud.get_all_filtered(
        name=library_in.name,
        git_url=library_in.git_url,
        use_or=True,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Library already exists",
        )
    return library_service.create(item_in=library_in)


@router.patch(
    "/{id}",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def update(
    *,
    library_service: LibraryAnnotations.LibraryService,
    library: LibraryAnnotations.GetLibrary,
    library_in: LibraryUpdate,
):
    return library_service.crud.update(
        item=library,
        item_in=library_in,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def delete(
    *,
    library_service: LibraryAnnotations.LibraryService,
    library: LibraryAnnotations.GetLibrary,
):
    return library_service.delete(item=library)


@router.put(
    "/{id}/sync",
    response_model=LibraryView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def resync(
    *,
    library: LibraryAnnotations.GetLibrary,
    library_service: LibraryAnnotations.LibraryService,
):
    return library_service.resync(library=library)
