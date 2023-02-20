import shutil

import git
from rich import print

from zpodapi.lib.utils import list_json_files
from zpodcommon import models as M


def zpod_create_library(library: M.Library):
    print(f"Creating Library: {library.name}...")
    repo = git.Repo.clone_from(library.git_url, f"/library/{library.name}")


def zpod_update_library(library: M.Library):
    print(f"Updating Library: {library.name}...")
    repo = git.Repo(f"/library/{library.name}")
    repo.remotes.origin.pull()


def zpod_delete_library(library: M.Library):
    print(f"Deleting Library: {library.name}...")
    shutil.rmtree(f"/library/{library.name}")


def zpod_fetch_library_components(library: M.Library):
    component_file_list = list_json_files(f"/library/{library.name}")

    print(component_file_list)
    return component_file_list
