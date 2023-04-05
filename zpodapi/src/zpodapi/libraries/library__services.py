import shutil

import git
from rich import print
from sqlmodel import SQLModel, select

from zpodapi.components.component__utils import get_component
from zpodapi.lib.service_base import ServiceBase
from zpodapi.lib.utils import list_json_files
from zpodcommon import models as M

from .library__schemas import LibraryCreate


class LibraryService(ServiceBase):
    base_model: SQLModel = M.Library

    def create(self, *, item_in: LibraryCreate):
        library = self.crud.create(item_in=item_in)

        # TODO: git clone git_url, and create all the components
        zpod_create_library(library)
        components_filename = zpod_fetch_library_components_filename(library)
        for component_filename in components_filename:
            component = get_component(component_filename)
            c = M.Component(
                library_name=item_in.name,
                filename=component_filename,
                enabled=False,
                status="",
                component_uid=(
                    f"{component['component_name']}-"
                    f"{component['component_version']}"
                ),
                component_name=component["component_name"],
                component_version=component["component_version"],
                component_description=component["component_description"],
            )
            self.session.add(c)
        self.session.commit()
        return library

    def delete(self, *, item: M.Library):
        statement = select(M.Component).where(M.Component.library_name == item.name)
        result = self.session.exec(statement)

        components = result.all()

        # Delete every component linked to Library to avoid FKEY violation
        for component in components:
            print(f"Deleting {component}")
            self.session.delete(component)
        self.session.commit()

        # Delete Library from DB
        print(f"Deleting {item.name}")
        self.crud.delete(item=item)

        # Delete Library from filesystem (not potential products download yet)
        zpod_delete_library(library=item)
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
