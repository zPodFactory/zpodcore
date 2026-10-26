from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodStorageFolderUpdate")


@_attrs_define
class ZpodStorageFolderUpdate:
    """
    Attributes:
        mode (None | str | Unset):
        owner (None | str | Unset):
        recursive (bool | Unset):  Default: False.
    """

    mode: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    recursive: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        mode: None | str | Unset
        if isinstance(self.mode, Unset):
            mode = UNSET
        else:
            mode = self.mode

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        recursive = self.recursive

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if owner is not UNSET:
            field_dict["owner"] = owner
        if recursive is not UNSET:
            field_dict["recursive"] = recursive

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_mode(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        mode = _parse_mode(d.pop("mode", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        recursive = d.pop("recursive", UNSET)

        zpod_storage_folder_update = cls(
            mode=mode,
            owner=owner,
            recursive=recursive,
        )

        return zpod_storage_folder_update
