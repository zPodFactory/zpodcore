from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_nfs_mounted_client import ZpodNfsMountedClient


T = TypeVar("T", bound="ZpodNfsStatus")


@_attrs_define
class ZpodNfsStatus:
    """
    Attributes:
        enabled (bool):
        exports (int):
        exports_in_files (int):
        service (str):
        versions (list[str]):
        clients (list[ZpodNfsMountedClient] | Unset):
        inactive_exports (list[str] | Unset):
        threads (int | None | Unset):
    """

    enabled: bool
    exports: int
    exports_in_files: int
    service: str
    versions: list[str]
    clients: list[ZpodNfsMountedClient] | Unset = UNSET
    inactive_exports: list[str] | Unset = UNSET
    threads: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        exports = self.exports

        exports_in_files = self.exports_in_files

        service = self.service

        versions = self.versions

        clients: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.clients, Unset):
            clients = []
            for clients_item_data in self.clients:
                clients_item = clients_item_data.to_dict()
                clients.append(clients_item)

        inactive_exports: list[str] | Unset = UNSET
        if not isinstance(self.inactive_exports, Unset):
            inactive_exports = self.inactive_exports

        threads: int | None | Unset
        if isinstance(self.threads, Unset):
            threads = UNSET
        else:
            threads = self.threads

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "exports": exports,
                "exports_in_files": exports_in_files,
                "service": service,
                "versions": versions,
            }
        )
        if clients is not UNSET:
            field_dict["clients"] = clients
        if inactive_exports is not UNSET:
            field_dict["inactive_exports"] = inactive_exports
        if threads is not UNSET:
            field_dict["threads"] = threads

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_nfs_mounted_client import ZpodNfsMountedClient

        d = dict(src_dict)
        enabled = d.pop("enabled")

        exports = d.pop("exports")

        exports_in_files = d.pop("exports_in_files")

        service = d.pop("service")

        versions = cast(list[str], d.pop("versions"))

        _clients = d.pop("clients", UNSET)
        clients: list[ZpodNfsMountedClient] | Unset = UNSET
        if _clients is not UNSET:
            clients = []
            for clients_item_data in _clients:
                clients_item = ZpodNfsMountedClient.from_dict(clients_item_data)

                clients.append(clients_item)

        inactive_exports = cast(list[str], d.pop("inactive_exports", UNSET))

        def _parse_threads(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        threads = _parse_threads(d.pop("threads", UNSET))

        zpod_nfs_status = cls(
            enabled=enabled,
            exports=exports,
            exports_in_files=exports_in_files,
            service=service,
            versions=versions,
            clients=clients,
            inactive_exports=inactive_exports,
            threads=threads,
        )

        zpod_nfs_status.additional_properties = d
        return zpod_nfs_status

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
