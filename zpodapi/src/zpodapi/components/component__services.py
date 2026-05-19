import os
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import ComponentDownloadStatus, ComponentStatus
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

PRODUCTS_PATH = "/products"


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
        self._remove_component_file(component)
        component.status = ComponentStatus.INACTIVE
        # The downloaded file is gone — reset so the state stays honest and a
        # later enable() re-downloads it.
        component.download_status = ComponentDownloadStatus.NOT_STARTED
        return self.crud.save(component)

    @staticmethod
    def _remove_component_file(component: M.Component) -> None:
        """Best-effort removal of a component's downloaded product file.

        The file lives at /products/<name>/<version>/<filename>; once removed,
        now-empty version/name directories are pruned. Filesystem errors are
        logged but never block the component from being disabled.
        """
        file_path = (
            Path(PRODUCTS_PATH)
            / component.component_name
            / component.component_version
            / component.filename
        )
        try:
            if file_path.is_file():
                file_path.unlink()
                print(f"Removed component file: {file_path}")
            # Prune now-empty parent directories (version, then name).
            for directory in (file_path.parent, file_path.parent.parent):
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()
        except OSError as e:
            print(f"Could not remove component file {file_path}: {e}")

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
