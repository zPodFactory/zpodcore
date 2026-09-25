from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ZpodNetworkView")


@_attrs_define
class ZpodNetworkView:
    """
    Attributes:
        cidr (str):
        id (int):
    """

    cidr: str
    id: int

    def to_dict(self) -> dict[str, Any]:
        cidr = self.cidr

        id = self.id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cidr": cidr,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cidr = d.pop("cidr")

        id = d.pop("id")

        zpod_network_view = cls(
            cidr=cidr,
            id=id,
        )

        return zpod_network_view
