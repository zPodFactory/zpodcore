from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums

from .zpod_nfs__schemas import ZboxView


class D:
    name = {"example": "STORAGE02"}
    disk = {"example": "/dev/sdc"}
    device = {"example": "/dev/sdc1"}
    folder = {"example": "DATASTORE01"}
    owner = {"example": "root:root"}
    mode = {"example": "0777"}


class ZpodStorageFolderView(ZboxView):
    name: str = Field(..., D.folder)
    path: str = Field(..., {"example": "/FILER/STORAGE02/DATASTORE01"})
    exported: bool = Field(...)
    protected: bool = Field(...)
    empty: bool = Field(...)
    mode: str = Field(..., D.mode)
    owner: str = Field(..., D.owner)


class ZpodStorageView(ZboxView):
    name: str = Field(..., D.name)
    mountpoint: str = Field(..., {"example": "/FILER/STORAGE02"})
    disk: str = Field(..., {"example": "sdc"})
    device: str = Field(..., D.device)
    layout: str = Field(..., {"example": "raw"})  # raw | lvm
    vg: str | None = Field(None)
    lv: str | None = Field(None)
    fstype: str | None = Field(None, {"example": "ext4"})
    uuid: str | None = Field(None)
    size_bytes: int = Field(...)
    used_bytes: int = Field(...)
    available_bytes: int = Field(...)
    protected: bool = Field(...)
    managed: bool = Field(...)
    exports: int = Field(...)
    folders: list[ZpodStorageFolderView] = Field([])
    # zcore: STORAGE01, built by zcore-init, grow only; user: the others.
    kind: enums.ZpodStorageKind = Field(enums.ZpodStorageKind.USER)


class ZpodStorageStep(ZboxView):
    step: str = Field(..., {"example": "mkfs"})
    target: str = Field(..., {"example": "/dev/sdc1"})
    detail: str = Field("")
    status: str = Field(..., {"example": "done"})
    exit_code: int | None = Field(None)
    command: str | None = Field(None)
    output: str | None = Field(None)


class ZpodStorageOperation(ZboxView):
    """zboxapi's answer to create, adopt, grow and delete: the step table."""

    operation: str = Field(..., {"example": "create"})
    name: str = Field(..., D.name)
    dry_run: bool = Field(...)
    storage: ZpodStorageView | None = Field(None)
    steps: list[ZpodStorageStep] = Field([])
    rollback: list[ZpodStorageStep] = Field([])
    changed: bool | None = Field(None)
    before: dict[str, int] | None = Field(None)
    after: dict[str, int] | None = Field(None)
    disk_state: str | None = Field(None)


class ZpodStorageCreate(SchemaBase):
    disk: str = Field(..., D.disk)
    # one VG per disk with one LV (D12: raw by default)
    lvm: bool = Field(False)
    # default: the next free STORAGEnn
    name: str | None = Field(None, D.name)


class ZpodStorageAdopt(SchemaBase):
    device: str = Field(..., D.device)
    name: str | None = Field(None, D.name)


class ZpodStorageFolderCreate(SchemaBase):
    owner: str | None = Field(None, D.owner)
    mode: str | None = Field(None, D.mode)


class ZpodStorageFolderUpdate(SchemaBase):
    owner: str | None = Field(None, D.owner)
    mode: str | None = Field(None, D.mode)
    recursive: bool = Field(False)


class ZpodStorageFolderRemoved(ZboxView):
    message: str = Field(...)
    path: str = Field(...)
    removed: int = Field(...)
    forced: bool = Field(...)
