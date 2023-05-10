import os
import shutil

import git
from rich import print
from sqlmodel import SQLModel, select

from zpodapi.components.component__utils import get_component
from zpodapi.lib.service_base import ServiceBase
from zpodapi.lib.utils import list_json_files
from zpodcommon.lib.zpodengine_client import ZpodEngineClient
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
            filename = os.path.basename(component["component_download_file"])
            c = M.Component(
                library_name=item_in.name,
                filename=filename,
                jsonfile=component_filename,
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

    def update(self, *, item_in: LibraryCreate):
        library = self.crud.get(id=item_in.id)
        # zpod_update_library(library=item_in)
        component_filename_list = zpod_fetch_library_components_filename(library)
        for component_filename in component_filename_list:
            component = get_component(component_filename)

            if component["component_name"] == "zpod-engine":
                continue
            statement = select(M.Component).where(
                M.Component.component_uid == f"{component['component_name']}-{component['component_version']}"
            )
            result = self.session.exec(statement).first()
            if result and result.active is True:
                updated_component = initialize_component(
                    component_filename=component_filename,
                    component=component,
                    library_name=library.name,
                    is_enabled=result.enabled,
                    is_active=True,
                    status=result.status,
                )
                for key, value in updated_component.items():
                    setattr(result, key, value)
                self.session.add(result)
                self.session.commit()

                zpod_engine = ZpodEngineClient()
                zpod_engine.create_flow_run_by_name(
                    flow_name="component_download",
                    deployment_name="default",
                    uid=result.component_uid,
                )

            if result is None:
                new_component = initialize_component(
                    component_filename=component_filename,
                    component=component,
                    library_name=library.name,
                    is_enabled=False,
                    is_active=False,
                    status=""
                )
                c = M.Component(**new_component)
                self.session.add(c)
                self.session.commit()

            else:
                print("No")
                # for key, value in hero_data.items():
                #     setattr(db_hero, key, value)
                # session.add(db_hero)
                # session.commit()
                # session.refresh(db_hero)
                # print("yes")
                # three possible cases:
                # if the component exists update the fields and if active kick off download
                # if the component does not exist create it
                # if the component is enabled q
            #
            #     continue:
            # else:
            #     #compose the component
            #     #add it to the db;


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


def initialize_component(
        library_name: str,
        component: dict,
        component_filename: str,
        is_enabled: bool = False,
        is_active: bool = False,
        status: str = ""):
    filename = os.path.basename(component["component_download_file"])
    return dict(
        library_name=library_name,
        filename=filename,
        jsonfile=component_filename,
        enabled=is_enabled,
        status=status,
        component_uid=(
            f"{component['component_name']}-"
            f"{component['component_version']}"
        ),
        component_name=component["component_name"],
        component_version=component["component_version"],
        component_description=component["component_description"],
        active=is_active,
    )
