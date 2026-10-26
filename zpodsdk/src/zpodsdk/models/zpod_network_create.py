from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.zpod_network_routing import ZpodNetworkRouting
from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodNetworkCreate")


@_attrs_define
class ZpodNetworkCreate:
    """
    Attributes:
        gateway (str):
        name (str):
        vlan (int):
        masquerade (bool | Unset):  Default: False.
        routing (ZpodNetworkRouting | Unset):
    """

    gateway: str
    name: str
    vlan: int
    masquerade: bool | Unset = False
    routing: ZpodNetworkRouting | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        gateway = self.gateway

        name = self.name

        vlan = self.vlan

        masquerade = self.masquerade

        routing: str | Unset = UNSET
        if not isinstance(self.routing, Unset):
            routing = self.routing.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "gateway": gateway,
                "name": name,
                "vlan": vlan,
            }
        )
        if masquerade is not UNSET:
            field_dict["masquerade"] = masquerade
        if routing is not UNSET:
            field_dict["routing"] = routing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        gateway = d.pop("gateway")

        name = d.pop("name")

        vlan = d.pop("vlan")

        masquerade = d.pop("masquerade", UNSET)

        _routing = d.pop("routing", UNSET)
        routing: ZpodNetworkRouting | Unset
        if isinstance(_routing, Unset):
            routing = UNSET
        else:
            routing = ZpodNetworkRouting(_routing)

        zpod_network_create = cls(
            gateway=gateway,
            name=name,
            vlan=vlan,
            masquerade=masquerade,
            routing=routing,
        )

        return zpod_network_create
