from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from rich import print
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, or_, select

from zpodapi import schemas as S
from zpodapi.lib import deps, libraries
from zpodcommon import models as M

router = APIRouter(
    tags=["libraries"],
    dependencies=[Depends(deps.get_current_user_and_update)],
)


async def get_library_record(
    *,
    session: Session = Depends(deps.get_session),
    name: str | None = None,
    git_url: str | None = None,
):
    try:
        return session.exec(
            select(M.Library).where(
                or_(
                    M.Library.name == name,
                    M.Library.git_url == git_url,
                )
            )
        ).one()
    except (NoResultFound, MultipleResultsFound) as e:
        raise HTTPException(status_code=404, detail="Library not found") from e


@router.get(
    "/libraries",
    response_model=list[S.LibraryView],
)
def get_all(
    *,
    session: Session = Depends(deps.get_session),
):
    return session.exec(select(M.Library)).all()


@router.post(
    "/libraries",
    response_model=S.LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def create(
    *,
    session: Session = Depends(deps.get_session),
    library: S.LibraryCreate,
):
    if session.exec(
        select(M.Library).where(
            or_(
                M.Library.name == library.name,
                M.Library.git_url == library.git_url,
            )
        )
    ).first():
        raise HTTPException(status_code=422, detail="Conflicting record found")

    db_library = M.Library(
        **library.dict(), creation_date=datetime.now(), lastupdate_date=datetime.now()
    )
    session.add(db_library)
    session.commit()
    session.refresh(db_library)

    # TODO: git clone git_url, and create all the components
    libraries.zpod_create_library(db_library)
    components_list = libraries.zpod_fetch_library_components(db_library)

    for component in components_list:
        c = M.Component(library_name=library.name, filename=component, enabled=False)
        session.add(c)
        session.commit()

    return db_library


@router.patch(
    "/libraries",
    response_model=S.LibraryView,
    status_code=status.HTTP_201_CREATED,
)
def update(
    *,
    session: Session = Depends(deps.get_session),
    db_library: M.Library = Depends(get_library_record),
    library: S.LibraryUpdate,
):
    for key, value in library.dict(exclude_unset=True).items():
        setattr(db_library, key, value)

    session.add(db_library)
    session.commit()
    session.refresh(db_library)
    return db_library


@router.delete(
    "/libraries",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    *,
    session: Session = Depends(deps.get_session),
    db_library: M.Library = Depends(get_library_record),
):
    statement = select(M.Component).where(M.Component.library_name == db_library.name)
    result = session.exec(statement)

    components = result.all()

    # Delete every component linked to Library to avoid FKEY violation
    for component in components:
        print(f"Deleting {component}")
        session.delete(component)

    session.commit()

    # Delete Library from DB
    print(f"Deleting {db_library}")
    session.delete(db_library)
    session.commit()

    # Delete Library from filesystem (not potential products download yet)
    libraries.zpod_delete_library(db_library)

    return None
