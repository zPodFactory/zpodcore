from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.zpod_network_kind import ZpodNetworkKind
from ..models.zpod_network_routing import ZpodNetworkRouting
from ..models.zpod_network_status import ZpodNetworkStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodNetworkView")


@_attrs_define
class ZpodNetworkView:
    """
    Attributes:
        cidr (str):
        gateway (str):
        kind (ZpodNetworkKind):
        masquerade (bool):
        name (str):
        routing (ZpodNetworkRouting):
        vlan_id (int):
        id (int | None | Unset):
        status (ZpodNetworkStatus | Unset):
    """

    cidr: str
    gateway: str
    kind: ZpodNetworkKind
    masquerade: bool
    name: str
    routing: ZpodNetworkRouting
    vlan_id: int
    id: int | None | Unset = UNSET
    status: ZpodNetworkStatus | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        cidr = self.cidr

        gateway = self.gateway

        kind = self.kind.value

        masquerade = self.masquerade

        name = self.name

        routing = self.routing.value

        vlan_id = self.vlan_id

        id: int | None | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cidr": cidr,
                "gateway": gateway,
                "kind": kind,
                "masquerade": masquerade,
                "name": name,
                "routing": routing,
                "vlan_id": vlan_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cidr = d.pop("cidr")

        gateway = d.pop("gateway")

        kind = ZpodNetworkKind(d.pop("kind"))

        masquerade = d.pop("masquerade")

        name = d.pop("name")

        routing = ZpodNetworkRouting(d.pop("routing"))

        vlan_id = d.pop("vlan_id")

        def _parse_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        _status = d.pop("status", UNSET)
        status: ZpodNetworkStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ZpodNetworkStatus(_status)

        zpod_network_view = cls(
            cidr=cidr,
            gateway=gateway,
            kind=kind,
            masquerade=masquerade,
            name=name,
            routing=routing,
            vlan_id=vlan_id,
            id=id,
            status=status,
        )

        return zpod_network_view
