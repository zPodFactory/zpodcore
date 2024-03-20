from ipaddress import IPv4Network

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    id = {"example": 1}
    cidr = {"example": "192.168.0.0/24"}


class ZpodNetworkView(SchemaBase):
    id: int = Field(..., D.id)
    cidr: IPv4Network = Field(..., D.cidr)
