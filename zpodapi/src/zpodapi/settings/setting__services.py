from rich import print
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .setting__schemas import SettingCreate, SettingUpdate


class SettingService(ServiceBase):
    base_model: SQLModel = M.Setting

    def create(self, *, item_in: SettingCreate):
        return self.crud.create(item_in=item_in)

    def update(self, *, item_in: SettingUpdate):
        return self.crud.update(item_in=item_in)

    def delete(self, *, item: M.Setting):
        # Delete Setting from DB
        print(f"Deleting {item.name}")
        self.crud.delete(item=item)
