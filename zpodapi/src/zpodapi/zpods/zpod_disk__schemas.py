from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums


class D:
    id = {"example": 3}
    device = {"example": "/dev/sdc"}
    scsi = {"example": "0:2"}
    size_gb = {"example": 500}
    state = {"example": "blank"}
    storage = {"example": "STORAGE02"}
    kind = {"example": enums.ZpodDiskKind.USER}
    status = {"example": enums.ZpodDiskStatus.ACTIVE}
    disk_uuid = {"example": "6000c29d7e62d7374a07e268ee051837"}
    flow_run_id = {"example": "8c1e0b2a-0000-4000-8000-000000000000"}
    run_name = {"example": "add disk demo/500GiB by admin"}
    run_state = {"example": "COMPLETED"}
    run_message = {"example": "All states completed."}


class ZpodDiskView(SchemaBase):
    # None for a disk zcore has that no row describes.
    id: int | None = Field(None, D.id)
    # Matched live by serial; None when zcore does not see the row's disk.
    device: str | None = Field(None, D.device)
    scsi: str | None = Field(None, D.scsi)
    # GiB (binary): what zcore sees, or the row's size when zcore does not see it.
    size_gb: int = Field(..., D.size_gb)
    # zboxapi's live classification: system, protected, blank, foreign, in-use.
    state: str | None = Field(None, D.state)
    storage: str | None = Field(None, D.storage)
    kind: enums.ZpodDiskKind = Field(..., D.kind)
    status: enums.ZpodDiskStatus = Field(..., D.status)
    disk_uuid: str | None = Field(None, D.disk_uuid)


class ZpodDiskCreate(SchemaBase):
    size_gb: int = Field(..., D.size_gb, ge=1)


class ZpodDiskGrow(SchemaBase):
    # The new total size, larger than the current one.
    size_gb: int = Field(..., {"example": 1000}, ge=1)


class ZpodDiskRunView(SchemaBase):
    # The disk as it is now; None once a remove deleted it.
    disk: ZpodDiskView | None = Field(None)
    flow_run_id: str | None = Field(None, D.flow_run_id)
    name: str | None = Field(None, D.run_name)
    state: str = Field("SCHEDULED", D.run_state)
    message: str | None = Field(None, D.run_message)
