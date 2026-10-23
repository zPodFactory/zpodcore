from ipaddress import IPv4Network
from typing import TYPE_CHECKING, Any

from sqlmodel import JSON, Column, Field, Relationship, UniqueConstraint

from zpodcommon import enums
from zpodcommon.models.model_base import ModelBase

from .mixins import CommonDatesMixin

if TYPE_CHECKING:
    from .component_models import Component
    from .endpoint_models import Endpoint
    from .permission_group_models import PermissionGroup
    from .user_models import User


class Zpod(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "zpods"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    name: str = Field(
        default=...,
        index=True,
        nullable=False,
    )
    description: str = Field(
        default="",
        nullable=False,
    )
    password: str = Field(
        default="",
        nullable=False,
    )
    domain: str = Field(
        default="",
        nullable=False,
    )
    profile: str = Field(
        default="",
        nullable=False,
    )
    endpoint_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="endpoints.id",
    )
    status: str = Field(
        default=...,
        nullable=False,
    )
    features: dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=False, index=False),
    )

    components: list["ZpodComponent"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    networks: list["ZpodNetwork"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
            # The four deploy-time rows come first, in creation order; user
            # networks append after them.
            "order_by": "ZpodNetwork.id",
        },
    )

    disks: list["ZpodDisk"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
            "order_by": "ZpodDisk.id",
        },
    )

    @property
    def mgmt_network(self) -> "ZpodNetwork":
        """The management /26 (native VLAN): every component address derives from it."""
        for network in self.networks:
            if network.kind == enums.ZpodNetworkKind.ZPOD and network.vlan_id == 0:
                return network
        return self.networks[0]

    @property
    def routed_networks(self) -> list["ZpodNetwork"]:
        """The deploy-time VLAN /26s the T1 routes to zcore (64/128/192)."""
        return [
            network
            for network in self.networks
            if network.kind == enums.ZpodNetworkKind.ZPOD and network.vlan_id != 0
        ]

    @property
    def user_networks(self) -> list["ZpodNetwork"]:
        return [
            network
            for network in self.networks
            if network.kind == enums.ZpodNetworkKind.USER
        ]

    permissions: list["ZpodPermission"] = Relationship(
        back_populates="zpod",
        sa_relationship_kwargs={
            "cascade": "all,delete,delete-orphan",
        },
    )
    endpoint: "Endpoint" = Relationship()


class ZpodComponent(CommonDatesMixin, ModelBase, table=True):
    __tablename__ = "zpod_components"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    component_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="components.id",
    )
    status: str = Field(
        default=...,
        nullable=False,
    )
    ip: str = Field(
        default=...,
        nullable=True,
    )
    hostname: str = Field(
        default=...,
        nullable=True,
    )
    fqdn: str = Field(
        default=...,
        nullable=True,
    )

    @property
    def password(self) -> str | None:
        return self.zpod.password if self.zpod else None

    @property
    def usernames(self) -> list[dict[str, str]] | None:
        if not self.zpod or not self.component:
            return None
        return self.component.get_usernames(
            zpod_domain=self.zpod.domain,
        )

    zpod: "Zpod" = Relationship(back_populates="components")
    component: "Component" = Relationship()


class ZpodNetwork(ModelBase, table=True):
    __tablename__ = "zpod_networks"
    __table_args__ = (
        UniqueConstraint(
            "zpod_id", "vlan_id", name="zpod_networks_zpod_id_vlan_id_key"
        ),
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    cidr: IPv4Network = Field(
        default=...,
        nullable=False,
    )
    # "mgmt", "vlan64", "vlan128", "vlan192" for the deploy rows; user-chosen otherwise.
    name: str = Field(
        default="",
        nullable=False,
    )
    # 0 is the native (untagged) VLAN, the management network.
    vlan_id: int = Field(
        default=0,
        nullable=False,
    )
    # The gateway address with its prefix, as given: "10.10.100.1/24".
    gateway: str = Field(
        default="",
        nullable=False,
    )
    # Stored as plain text like Zpod.status (an Enum-typed field would make
    # SQLModel store the member name); values are enums.ZpodNetworkKind.
    kind: str = Field(
        default=enums.ZpodNetworkKind.ZPOD.value,
        nullable=False,
    )
    # Source translation on zcore for this subnet (zboxapi masquerade); the live
    # value is read from zboxapi on every list, this is what was asked for.
    masquerade: bool = Field(
        default=False,
        nullable=False,
    )
    # Values are enums.ZpodNetworkRouting (LOCAL, GLOBAL, PENDING), stored as text.
    routing: str = Field(
        default=enums.ZpodNetworkRouting.LOCAL.value,
        nullable=False,
    )

    zpod: "Zpod" = Relationship(back_populates="networks")

    @classmethod
    def deploy_row(cls, cidr: IPv4Network) -> "ZpodNetwork":
        """One of the four deploy-time rows, named and typed from its /26."""
        vlan_id = int(str(cidr.network_address).split(".")[-1])
        return cls(
            # Stored as text (AutoString); readers wrap it in IPv4Network.
            cidr=str(cidr),
            name="mgmt" if vlan_id == 0 else f"vlan{vlan_id}",
            vlan_id=vlan_id,
            gateway=f"{cidr.network_address + 1}/{cidr.prefixlen}",
            kind=enums.ZpodNetworkKind.ZPOD.value,
            masquerade=False,
            # The native /26 is the T1 segment itself, the other three are
            # routed to zcore by static routes: all four are reachable from
            # the fabric.
            routing=enums.ZpodNetworkRouting.GLOBAL.value,
        )


def normalise_disk_uuid(uuid: str | None) -> str | None:
    """vSphere's backing.uuid (6000C29d-7e62-...) and the guest's lsblk serial
    (6000c29d7e62...) compare equal once reduced to lowercase hex."""
    if not uuid:
        return None
    return "".join(c for c in uuid.lower() if c in "0123456789abcdef") or None


class ZpodDisk(ModelBase, table=True):
    """A virtual disk of the zPod's zcore VM.

    The row holds the vSphere handles (device key, SCSI unit, disk UUID) and the
    size asked for; the device name (/dev/sdX) is never stored, it is matched live
    by serial = disk_uuid (disk.EnableUUID). What is on the disk is zboxapi's.
    """

    __tablename__ = "zpod_disks"
    __table_args__ = (
        UniqueConstraint(
            "zpod_id", "scsi_unit", name="zpod_disks_zpod_id_scsi_unit_key"
        ),
        UniqueConstraint(
            "zpod_id", "disk_uuid", name="zpod_disks_zpod_id_disk_uuid_key"
        ),
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    # enums.ZpodDiskKind, stored as text.
    kind: str = Field(
        default=enums.ZpodDiskKind.USER.value,
        nullable=False,
    )
    # ACTIVE or PENDING (enums.ZpodDiskStatus), stored as text.
    status: str = Field(
        default=enums.ZpodDiskStatus.PENDING.value,
        nullable=False,
    )
    # GiB, binary: the size asked for, then the size vCenter reports.
    size_gb: int = Field(
        default=...,
        nullable=False,
    )
    # Unit on the zcore VM's first SCSI controller; None until the add flow
    # picks it.
    scsi_unit: int | None = Field(
        default=None,
        nullable=True,
    )
    # VirtualDevice.key; vCenter gives a freed key to the next disk added, so it
    # is only trusted together with disk_uuid.
    vm_disk_key: int | None = Field(
        default=None,
        nullable=True,
    )
    # VirtualDisk.backing.uuid, normalised (normalise_disk_uuid): the guest's
    # serial of the disk.
    disk_uuid: str | None = Field(
        default=None,
        nullable=True,
    )

    zpod: "Zpod" = Relationship(back_populates="disks")


class ZpodPermission(ModelBase, table=True):
    __tablename__ = "zpod_permissions"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
    )
    zpod_id: int = Field(
        default=...,
        nullable=False,
        foreign_key="zpods.id",
    )
    permission: str = Field(
        default=...,
        nullable=False,
    )

    zpod: "Zpod" = Relationship(back_populates="permissions")
    users: list["User"] = Relationship(
        back_populates="zpod_permissions",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_user_link",
        },
    )
    permission_groups: list["PermissionGroup"] = Relationship(
        back_populates="zpod_permissions",
        sa_relationship_kwargs={
            "secondary": "zpod_permission_group_link",
        },
    )


class ZpodPermissionUserLink(ModelBase, table=True):
    __tablename__ = "zpod_permission_user_link"

    zpod_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="zpod_permissions.id",
    )
    user_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="users.id",
    )


class ZpodPermissionGroupLink(ModelBase, table=True):
    __tablename__ = "zpod_permission_group_link"

    zpod_permission_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="zpod_permissions.id",
    )
    permission_group_id: int = Field(
        default=...,
        primary_key=True,
        nullable=False,
        foreign_key="permission_groups.id",
    )
