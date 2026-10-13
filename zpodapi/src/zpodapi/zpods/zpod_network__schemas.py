from ipaddress import IPv4Network

from pydantic import field_validator

from zpodapi.lib.schema_base import Field, SchemaBase
from zpodcommon import enums


class D:
    id = {"example": 1}
    name = {"example": "LOCALNET111"}
    cidr = {"example": "10.42.111.0/24"}
    vlan = {"example": 111}
    gateway = {"example": "10.42.111.1/24"}
    kind = {"example": enums.ZpodNetworkKind.USER}
    masquerade = {"example": False}
    routing = {"example": enums.ZpodNetworkRouting.LOCAL}
    status = {"example": enums.ZpodNetworkStatus.ACTIVE}
    enabled = {"example": True}
    dry_run = {"example": False}
    flow_run_id = {"example": "5b1e0c3a-0000-4000-8000-000000000000"}
    run_name = {"example": "advertise demo/LOCALNET111 by admin"}
    run_state = {"example": "COMPLETED"}
    run_message = {"example": "All states completed."}


class ZpodNetworkView(SchemaBase):
    # None for the zcore-kind rows, which exist on the box only.
    id: int | None = Field(None, D.id)
    name: str = Field(..., D.name)
    cidr: IPv4Network = Field(..., D.cidr)
    vlan_id: int = Field(..., D.vlan)
    gateway: str = Field(..., D.gateway)
    kind: enums.ZpodNetworkKind = Field(..., D.kind)
    masquerade: bool = Field(..., D.masquerade)
    routing: enums.ZpodNetworkRouting = Field(..., D.routing)
    # Read live from zboxapi on every list, never stored.
    status: enums.ZpodNetworkStatus = Field(enums.ZpodNetworkStatus.UNKNOWN, D.status)


class ZpodNetworkCreate(SchemaBase):
    name: str = Field(..., D.name, min_length=1, max_length=32)
    vlan: int = Field(..., D.vlan, ge=1, le=4094)
    gateway: str = Field(..., D.gateway)
    masquerade: bool = Field(False, D.masquerade)
    routing: enums.ZpodNetworkRouting = Field(enums.ZpodNetworkRouting.LOCAL, D.routing)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()  # case kept as typed; lookups are case-insensitive
        if (
            not value.replace("-", "").replace("_", "").isalnum()
            or not value[0].isalpha()
        ):
            raise ValueError(
                "name must start with a letter and contain only letters, digits, '-' or '_'"
            )
        return value

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, value: str) -> str:
        # Interface-style address: a host address with its prefix.
        try:
            address, prefix = value.split("/")
            network = IPv4Network(f"{address}/{prefix}", strict=False)
        except ValueError as e:
            raise ValueError(
                "gateway must be an IPv4 address with a prefix, like 10.42.111.1/24"
            ) from e
        if network.prefixlen > 30 or network.prefixlen < 8:
            raise ValueError("gateway prefix must be between /8 and /30")
        host = IPv4Network(f"{address}/32").network_address
        if host in (network.network_address, network.broadcast_address):
            raise ValueError(
                "gateway must be a host address, not the network or broadcast"
            )
        return value

    @field_validator("routing")
    @classmethod
    def validate_routing(
        cls, value: enums.ZpodNetworkRouting
    ) -> enums.ZpodNetworkRouting:
        if value == enums.ZpodNetworkRouting.PENDING:
            raise ValueError("routing must be local or global")
        return value


class ZpodNetworkMasquerade(SchemaBase):
    enabled: bool = Field(..., D.enabled)


class ZpodNetworkRoutingUpdate(SchemaBase):
    routing: enums.ZpodNetworkRouting = Field(..., D.routing)
    dry_run: bool = Field(False, D.dry_run)

    @field_validator("routing")
    @classmethod
    def validate_routing(
        cls, value: enums.ZpodNetworkRouting
    ) -> enums.ZpodNetworkRouting:
        if value == enums.ZpodNetworkRouting.PENDING:
            raise ValueError("routing must be local or global")
        return value


class ZpodNetworkRoutingView(SchemaBase):
    network: ZpodNetworkView
    # Set when a flow was scheduled; absent when nothing had to change.
    flow_run_id: str | None = Field(None, D.flow_run_id)


class ZpodNetworkRoutingRunView(SchemaBase):
    """A routing flow run as zpodengine reports it, with the network as it is now."""

    network: ZpodNetworkView
    flow_run_id: str = Field(..., D.flow_run_id)
    name: str | None = Field(None, D.run_name)
    # Prefect state type: SCHEDULED, PENDING, RUNNING, COMPLETED, FAILED, CRASHED, CANCELLED
    state: str = Field(..., D.run_state)
    # Prefect's state message; for a failed run the failing check, e.g.
    # "FAIL: 10.42.111.0/24 overlaps 10.42.0.0/16 from the routing table of T0 ..."
    message: str | None = Field(None, D.run_message)
