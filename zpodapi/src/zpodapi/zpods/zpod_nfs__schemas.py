import ipaddress

from pydantic import ConfigDict, field_validator

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    storage = {"example": "STORAGE02"}
    folder = {"example": "DATASTORE01"}
    path = {"example": "/FILER/STORAGE02/DATASTORE01"}
    client = {"example": "10.42.111.0/24"}
    clients = {"example": ["10.42.111.0/24"]}
    options = {"example": "rw,no_subtree_check,no_root_squash"}
    owner = {"example": "user-defined"}
    message = {"example": "/FILER/STORAGE02/DATASTORE01 is no longer exported"}


def validate_client(value: str) -> str:
    """An IPv4 address, an IPv4 network in CIDR notation, or * for everyone."""
    value = value.strip()
    if value == "*":
        return value
    try:
        if "/" in value:
            ipaddress.IPv4Network(value, strict=False)
        else:
            ipaddress.IPv4Address(value)
    except ValueError as e:
        raise ValueError(
            f"invalid client '{value}': an IPv4 address, an IPv4 network such as "
            "10.42.111.0/24, or * for everyone"
        ) from e
    return value


class ZboxView(SchemaBase):
    """What zboxapi answers, passed through: a newer zboxapi may add fields."""

    model_config = ConfigDict(extra="ignore")


class ZpodNfsClientView(ZboxView):
    client: str = Field(..., D.client)
    options: str = Field(..., D.options)


class ZpodNfsExportView(ZboxView):
    path: str = Field(..., D.path)
    # None for an export outside /FILER/<storage>/<folder>
    storage: str | None = Field(None, D.storage)
    folder: str | None = Field(None, D.folder)
    options: str = Field(..., D.options)
    clients: list[ZpodNfsClientView] = Field(...)
    owner: str = Field(..., D.owner)  # system (/etc/exports) | user-defined
    protected: bool = Field(...)
    active: bool = Field(...)
    folder_exists: bool = Field(True)


class ZpodNfsExportRemoved(ZboxView):
    message: str = Field(..., D.message)
    path: str = Field(..., D.path)
    folder_kept: bool = Field(True)


class ZpodNfsMountedClient(ZboxView):
    client: str = Field(..., {"example": "10.42.111.11"})
    path: str | None = Field(None, D.path)  # NFSv3 only
    version: str = Field(..., {"example": "3"})


class ZpodNfsStatus(ZboxView):
    service: str = Field(..., {"example": "active"})
    enabled: bool = Field(...)
    versions: list[str] = Field(..., {"example": ["3", "4", "4.1", "4.2"]})
    threads: int | None = Field(None, {"example": 16})
    exports: int = Field(..., {"example": 2})
    exports_in_files: int = Field(..., {"example": 2})
    inactive_exports: list[str] = Field([])
    clients: list[ZpodNfsMountedClient] = Field([])


class ZpodNfsCreate(SchemaBase):
    storage: str = Field(..., D.storage)
    folder: str = Field(..., D.folder)
    # zboxapi needs at least one client; none given means * (D13)
    clients: list[str] | None = Field(None, D.clients)
    options: str | None = Field(None, D.options)

    @field_validator("clients")
    @classmethod
    def check_clients(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if not value:
            raise ValueError("give at least one client, or none for * (any host)")
        return [validate_client(c) for c in value]


class ZpodNfsUpdate(SchemaBase):
    clients: list[str] = Field(..., D.clients, min_length=1)
    # omitted keeps the export's current options
    options: str | None = Field(None, D.options)

    @field_validator("clients")
    @classmethod
    def check_clients(cls, value: list[str]) -> list[str]:
        return [validate_client(c) for c in value]


class ZpodNfsClientAdd(SchemaBase):
    client: str = Field(..., D.client)

    @field_validator("client")
    @classmethod
    def check_client(cls, value: str) -> str:
        return validate_client(value)
