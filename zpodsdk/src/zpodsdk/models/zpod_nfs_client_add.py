from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ZpodNfsClientAdd")


@_attrs_define
class ZpodNfsClientAdd:
    """
    Attributes:
        client (str):
    """

    client: str

    def to_dict(self) -> dict[str, Any]:
        client = self.client

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "client": client,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client = d.pop("client")

        zpod_nfs_client_add = cls(
            client=client,
        )

        return zpod_nfs_client_add
