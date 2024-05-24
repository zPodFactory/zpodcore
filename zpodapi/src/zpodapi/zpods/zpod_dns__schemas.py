from ipaddress import IPv4Address

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodapi.lib.types import HOSTNAME


class D:
    ip = {"example": "10.20.30.11"}
    hostname = {"example": "esxi11"}
    host_id = {"example": 12}


class ZpodDnsView(SchemaBase):
    ip: IPv4Address = Field(..., D.ip)
    hostname: str = Field(..., D.hostname)


class ZpodDnsCreate(SchemaBase):
    ip: IPv4Address | None = Field(None, D.ip)
    host_id: int | None = Field(None, D.host_id, ge=0, le=255)
    hostname: HOSTNAME = Field(..., D.hostname)


class ZpodDnsUpdate(SchemaBase):
    ip: IPv4Address | None = Field(None, D.ip)
    host_id: int | None = Field(None, D.host_id, ge=0, le=255)
    hostname: HOSTNAME = Field(..., D.hostname)
