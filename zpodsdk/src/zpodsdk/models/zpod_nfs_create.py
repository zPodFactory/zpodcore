from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodNfsCreate")


@_attrs_define
class ZpodNfsCreate:
    """
    Attributes:
        folder (str):
        storage (str):
        clients (list[str] | None | Unset):
        options (None | str | Unset):
    """

    folder: str
    storage: str
    clients: list[str] | None | Unset = UNSET
    options: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        folder = self.folder

        storage = self.storage

        clients: list[str] | None | Unset
        if isinstance(self.clients, Unset):
            clients = UNSET
        elif isinstance(self.clients, list):
            clients = self.clients

        else:
            clients = self.clients

        options: None | str | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        else:
            options = self.options

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "folder": folder,
                "storage": storage,
            }
        )
        if clients is not UNSET:
            field_dict["clients"] = clients
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        folder = d.pop("folder")

        storage = d.pop("storage")

        def _parse_clients(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                clients_type_0 = cast(list[str], data)

                return clients_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        clients = _parse_clients(d.pop("clients", UNSET))

        def _parse_options(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        zpod_nfs_create = cls(
            folder=folder,
            storage=storage,
            clients=clients,
            options=options,
        )

        return zpod_nfs_create
