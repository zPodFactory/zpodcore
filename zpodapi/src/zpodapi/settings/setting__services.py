import shutil

import git
from rich import print
from sqlmodel import SQLModel, select

from zpodapi.components.component__utils import get_component
from zpodapi.lib.service_base import ServiceBase
from zpodapi.lib.utils import list_json_files
from zpodcommon import models as M

from .setting__schemas import SettingCreate, SettingUpdate


class SettingService(ServiceBase):
    base_model: SQLModel = M.Setting

    def create(self, *, item_in: SettingCreate):
        setting = self.crud.create(item_in=item_in)

        return setting

    def update(self, *, item_in: SettingUpdate):
        setting = self.crud.update(item_in=item_in)

        return setting

    def delete(self, *, item: M.Setting):
        # Delete Setting from DB
        print(f"Deleting {item.name}")
        self.crud.delete(item=item)
