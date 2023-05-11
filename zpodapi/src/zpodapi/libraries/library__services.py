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
                enabled=False,
                status="",
                component_uid=(
                    f"{component['component_name']}-"
                    f"{component['component_version']}"
                ),
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

    def update(self, *, item_in: LibraryCreate, db_components: M.Component):
        library = self.crud.get(id=item_in.id)

        zpod_update_library(library=item_in)

        component_filename_list = zpod_fetch_library_components_filename(library)

        updated_components = [get_component(comp_file) for comp_file in component_filename_list]
        component_uids = [get_component_uid(comp) for comp in updated_components]
        removed_components = [comp for comp in db_components if comp.component_uid not in component_uids]

        for item in updated_components:
            component_uid = get_component_uid(item)
            component_filename = get_component_jsonfile(item["component_version"],component_filename_list)
            if item["component_name"] == "zpod-engine":
                continue
            db_component = check_for_component(component_uid, db_components)
            if db_component and db_component.active is True:
                updated_component = initialize_component(
                    component_filename=component_filename,
                    component=item,
                    library_name=library.name,
                    is_enabled=db_component.enabled,
                    is_active=db_component.active,
                    status=db_component.status,
                )
                result = self.session.query(M.Component).filter(M.Component.component_uid == component_uid).first()
                for key, value in updated_component.items():
                    setattr(result, key, value)
                self.session.add(result)
                self.session.commit()

                # add download the component
                zpod_engine = ZpodEngineClient()
                zpod_engine.create_flow_run_by_name(
                    flow_name="component_download",
                    deployment_name="default",
                    uid=result.component_uid,
                )
                return library

            if db_component is None:
                new_component = initialize_component(
                    component_filename=component_filename,
                    component=item,
                    library_name=library.name,
                    is_enabled=False,
                    is_active=False,
                    status=""
                )
                c = M.Component(**new_component)
                self.session.add(c)
                self.session.commit()
                return library

        for comp in removed_components:
            result = self.session.query(M.Component).filter(M.Component.component_uid == comp.component_uid).first()
            result.status = CS.DELETED
            result.enabled = False
            result.active = False
            self.session.add(result)
            self.session.commit()
        return library


def get_component_jsonfile(component_version, component_filelist):
    for comp_file in component_filelist:
        version = Path(comp_file).stem
        if version == component_version:
            return comp_file


def get_component_uid(component):
    return f"{component['component_name']}-{component['component_version']}"


def check_for_component(component_id: str, results: list):
    filtered_results = filter(lambda x: x.component_uid == component_id, results)
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
