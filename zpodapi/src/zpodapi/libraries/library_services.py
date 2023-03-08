import shutil
from datetime import datetime

import git
from rich import print
from sqlmodel import Session, or_, select

from zpodapi.components.component_utils import get_component
from zpodapi.lib.utils import list_json_files
from zpodcommon import models as M

from .library_schemas import LibraryCreate, LibraryUpdate


def get_all(session: Session):
    return session.exec(select(M.Library)).all()


def get(
    session: Session,
    *,
    name: str | None = None,
    git_url: str | None = None,
):
    return session.exec(
        select(M.Library).where(
            or_(
                M.Library.name == name,
                M.Library.git_url == git_url,
            )
        )
    ).first()


def create(session: Session, *, library_in: LibraryCreate):
    library = M.Library(**library_in.dict(), creation_date=datetime.now())
    session.add(library)
    session.commit()
    session.refresh(library)

    # TODO: git clone git_url, and create all the components
    zpod_create_library(library)
    components_filename = zpod_fetch_library_components_filename(library)
    for component_filename in components_filename:
        component = get_component(component_filename)
        c = M.Component(
            library_name=library_in.name,
            filename=component_filename,
            enabled=False,
            status="",
            component_uid=f"{component['component_name']}-{component['component_version']}",
            component_name=component["component_name"],
            component_version=component["component_version"],
        )
        session.add(c)
    session.commit()

    return library


def update(session: Session, *, library: M.Library, library_in: LibraryUpdate):
    for key, value in library_in.dict(exclude_unset=True).items():
        setattr(library, key, value)

    session.add(library)
    session.commit()
    session.refresh(library)
    return library


def delete(session: Session, *, library: M.Library):
    statement = select(M.Component).where(M.Component.library_name == library.name)
    result = session.exec(statement)

    components = result.all()

    # Delete every component linked to Library to avoid FKEY violation
    for component in components:
        print(f"Deleting {component}")
        session.delete(component)

    session.commit()

    # Delete Library from DB
    print(f"Deleting {library}")
    session.delete(library)
    session.commit()

    # Delete Library from filesystem (not potential products download yet)
    zpod_delete_library(library)
    return None


def zpod_create_library(library: M.Library):
    print(f"Creating Library: {library.name}...")
    git.Repo.clone_from(library.git_url, f"/library/{library.name}")


def zpod_update_library(library: M.Library):
    print(f"Updating Library: {library.name}...")
    repo = git.Repo(f"/library/{library.name}")
    repo.remotes.origin.pull()


def zpod_delete_library(library: M.Library):
    print(f"Deleting Library: {library.name}...")
    shutil.rmtree(f"/library/{library.name}")


def zpod_fetch_library_components_filename(library: M.Library):
    component_file_list = list_json_files(f"/library/{library.name}")

    print(component_file_list)
    return component_file_list
