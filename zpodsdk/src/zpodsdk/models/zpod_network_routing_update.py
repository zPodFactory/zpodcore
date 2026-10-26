from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.zpod_network_routing import ZpodNetworkRouting
from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodNetworkRoutingUpdate")


@_attrs_define
class ZpodNetworkRoutingUpdate:
    """
    Attributes:
        routing (ZpodNetworkRouting):
        dry_run (bool | Unset):  Default: False.
    """

    routing: ZpodNetworkRouting
    dry_run: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        routing = self.routing.value

        dry_run = self.dry_run

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "routing": routing,
            }
        )
        if dry_run is not UNSET:
            field_dict["dry_run"] = dry_run

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        routing = ZpodNetworkRouting(d.pop("routing"))

        dry_run = d.pop("dry_run", UNSET)

        zpod_network_routing_update = cls(
            routing=routing,
            dry_run=dry_run,
        )

        return zpod_network_routing_update
