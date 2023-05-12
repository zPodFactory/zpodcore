import os
import shutil
from pathlib import Path
import git
from rich import print
from sqlmodel import SQLModel, select

from zpodapi.components.component__utils import get_component
from zpodcommon.enums import ComponentStatus as CS
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
                status=CS.INACTIVE,
                download_status=CS.NOT_STARTED,
                component_uid=get_component_uid(component),
                component_name=component["component_name"],
                component_version=component["component_version"],
                component_description=component["component_description"],
                active=False,
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

    def update(self, *, library: M.Library):
        db_components = self.crud.get_all(M.Component)
        zpod_update_library(library=library)

        git_component_filename_list = zpod_fetch_library_components_filename(library)
        git_components = [
            get_component(comp_file) for comp_file in git_component_filename_list
        ]
        git_component_uids = [get_component_uid(comp) for comp in git_components]

        # Resolving  differences between git_components and db/downloaded components
        for item in git_components:
            component_uid = get_component_uid(item)
            component_filename = get_component_jsonfile(
                item["component_version"], git_component_filename_list
            )
            if item["component_name"] == "zpod-engine":
                continue

            component = check_for_component(component_uid, db_components)

            # update component
            if component:
                updated_component = initialize_component(
                    component_filename=component_filename,
                    git_component=item,
                    library_name=library.name,
                    status=component.status,
                )

                for key, value in updated_component.items():
                    setattr(component, key, value)
                self.session.add(component)
                self.session.commit()

                # Download files if component is active
                if component.status == CS.ACTIVE:
                    zpod_engine = ZpodEngineClient()
                    zpod_engine.create_flow_run_by_name(
                        flow_name="component_download",
                        deployment_name="default",
                        uid=component.component_uid,
                    )
                continue

            # create new component if it does not exist in db
            if component is None:
                new_component = initialize_component(
                    component_filename=component_filename,
                    git_component=item,
                    library_name=library.name,
                    status=CS.INACTIVE,
                    download_status=CS.NOT_STARTED,
                )
                c = M.Component(**new_component)
                self.session.add(c)
                self.session.commit()
                continue

        # Marking deleted components in DB
        removed_components = [
            comp
            for comp in db_components
            if comp.component_uid not in git_component_uids
        ]
        for comp in removed_components:
            comp.status = CS.DELETED
            self.session.add(comp)
            self.session.commit()
        return library


def get_component_jsonfile(component_version, component_filelist):
    for comp_file in component_filelist:
        version = Path(comp_file).stem
        if version == component_version:
            return comp_file


def get_component_uid(component):
    return f"{component['component_name']}-{component['component_version']}"


def check_for_component(component_uid: str, results: list):
    filtered_results = filter(lambda x: x.component_uid == component_uid, results)
    return next(iter(filtered_results), None)


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
    git_component: dict,
    component_filename: str,
    download_status: str = "",
    status: str = "",
):
    filename = os.path.basename(git_component["component_download_file"])
    return dict(
        library_name=library_name,
        filename=filename,
        jsonfile=component_filename,
        status=status,
        download_status=download_status,
        component_uid=get_component_uid(git_component),
        component_name=git_component["component_name"],
        component_version=git_component["component_version"],
        component_description=git_component["component_description"],
    )
