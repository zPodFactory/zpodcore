import os
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ComponentDownloadStatus, ComponentStatus
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class ComponentService(ServiceBase):
    base_model: SQLModel = M.Component

    def enable(self, *, component: M.Component):
        if (
            component.download_status == ComponentDownloadStatus.COMPLETED
            and component.status == ComponentStatus.ACTIVE
        ):
            return component
        component.download_status = ComponentDownloadStatus.SCHEDULED
        self.crud.save(component)

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="component_download",
            deployment_name="component_download",
            uid=component.component_uid,
        )
        return component

    def disable(self, *, component: M.Component):
        component.status = ComponentStatus.INACTIVE
        return self.crud.save(component)

    async def upload(
        self,
        *,
        file: BinaryIO,
        filename: str,
        offset: int,
        file_size: int,
    ) -> int:
        file_location = os.path.join("/products", filename)

        # Check if the file exists and handle accordingly
        if os.path.exists(file_location):
            current_size = os.path.getsize(file_location)
            if offset != current_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Offset does not match the current file size.",
                )
        elif offset != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not exist, offset must be 0.",
            )

        with open(file_location, "ab") as f:
            f.seek(offset)
            f.write(await file.read())

        current_size = os.path.getsize(file_location)
        if current_size == file_size:
            self.sync(filename=filename)
        return current_size

    async def upload_filesize(self, *, filename: str):
        file_location = os.path.join("/products", filename)
        return os.path.getsize(file_location) if os.path.exists(file_location) else 0

    def sync(self, *, filename: str):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="component_sync",
            deployment_name="component_sync",
            filename=filename,
        )
