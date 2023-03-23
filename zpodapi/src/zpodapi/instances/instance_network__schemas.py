from ipaddress import IPv4Network

from sqlmodel import SQLModel

from zpodapi.lib.schema_base import Req


class InstanceNetworkView(SQLModel):
    id: int = Req(example=1)
    cidr: IPv4Network = Req(example=1)
