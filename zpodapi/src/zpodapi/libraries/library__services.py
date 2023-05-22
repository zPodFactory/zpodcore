import os
import shutil
from typing import List

import git
from rich import print
from sqlmodel import SQLModel, select

from zpodapi.components.component__utils import get_component
from zpodapi.lib.service_base import ServiceBase
from zpodapi.lib.utils import list_jsonfiles
from zpodcommon import models as M
from zpodcommon.enums import ComponentDownloadStatus, ComponentStatus
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from .library__schemas import LibraryCreate


class LibraryService(ServiceBase):
    base_model: SQLModel = M.Library

    def create(self, *, item_in: LibraryCreate):
        library = self.crud.create(item_in=item_in)

        # TODO: git clone git_url, and create all the components
        create_library(library)
        component_jsonfiles = list_jsonfiles(f"/library/{library.name}")
        for component_jsonfile in component_jsonfiles:
            git_component = get_component(component_jsonfile)
            component_dict = create_component_dict(
                library_name=item_in.name,
                component_jsonfile=component_jsonfile,
                git_component=git_component,
            )
            self.session.add(M.Component(**component_dict))
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
        delete_library(library=item)
        return None

    def sync(self, *, library: M.Library):
        update_library(library=library)

        db_components = self.crud.get_all(M.Component)

        component_jsonfiles = list_jsonfiles(f"/library/{library.name}")

        git_components = []

        # Resolving  differences between git_components and db/downloaded components
        for component_jsonfile in component_jsonfiles:
            git_component = get_component(component_jsonfile)
            git_components.append(git_component)
            component_uid = get_component_uid(git_component)

            component = find_component_by_uid(db_components, component_uid)

            component_dict = (
                create_component_dict(
                    status=component.status,
                    download_status=component.download_status,
                    component_jsonfile=component_jsonfile,
                    git_component=git_component,
                    library_name=library.name,
                )
                if component
                else create_component_dict(
                    component_jsonfile=component_jsonfile,
                    git_component=git_component,
                    library_name=library.name,
                )
            )

            # update existing component
            if component:
                update_component(component, component_dict, self.session)
                if component.status == ComponentStatus.ACTIVE:
                    download_component(component.component_uid)
            else:
                create_component(component_dict, self.session)

        # mark deleted components
        git_component_uids = [get_component_uid(comp) for comp in git_components]
        for component in db_components:
            if component.component_uid not in git_component_uids:
                mark_component_deleted(component, self.session)

        self.session.commit()
        return library


def get_component_uid(component):
    return f"{component['component_name']}-{component['component_version']}"


def find_component_by_uid(components: List[M.Component], uid: str) -> M.Component:
    return next((comp for comp in components if comp.component_uid == uid), None)


def create_component(component_dict, session):
    component = M.Component(**component_dict)
    session.add(component)


def download_component(component_uid: str):
    zpod_engine = ZpodEngineClient()
    zpod_engine.create_flow_run_by_name(
        flow_name="component_download",
        deployment_name="default",
        uid=component_uid,
    )


def mark_component_deleted(component, session):
    component.status = ComponentStatus.DELETED
    session.add(component)


def create_library(library: M.Library):
    print(f"Creating Library: {library.name}...")
    git.Repo.clone_from(library.git_url, f"/library/{library.name}")


def update_library(library: M.Library):
    print(f"Updating Library: {library.name}...")
    repo = git.Repo(f"/library/{library.name}")
    repo.remotes.origin.pull()


def delete_library(library: M.Library):
    print(f"Deleting Library: {library.name}...")
    shutil.rmtree(f"/library/{library.name}")


def update_component(component, modified_component, session):
    for key, value in modified_component.items():
        setattr(component, key, value)


def create_component_dict(
    library_name: str,
    git_component: dict,
    component_jsonfile: str,
    download_status: str = ComponentDownloadStatus.NOT_STARTED,
    status: str = ComponentStatus.INACTIVE,
):
    filename = os.path.basename(git_component["component_download_file"])
    return {
        "library_name": library_name,
        "filename": filename,
        "jsonfile": component_jsonfile,
        "status": status,
        "download_status": download_status,
        "component_uid": get_component_uid(git_component),
        **{
            k: v
            for k, v in git_component.items()
            if k in ["component_name", "component_version", "component_description"]
        },
    }
