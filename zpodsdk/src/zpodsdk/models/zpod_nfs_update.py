from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodNfsUpdate")


@_attrs_define
class ZpodNfsUpdate:
    """
    Attributes:
        clients (list[str]):
        options (None | str | Unset):
    """

    clients: list[str]
    options: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        clients = self.clients

        options: None | str | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        else:
            options = self.options

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "clients": clients,
            }
        )
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        clients = cast(list[str], d.pop("clients"))

        def _parse_options(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        zpod_nfs_update = cls(
            clients=clients,
            options=options,
        )

        return zpod_nfs_update
