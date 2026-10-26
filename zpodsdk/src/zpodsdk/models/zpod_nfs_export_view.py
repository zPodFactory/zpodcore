from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_nfs_client_view import ZpodNfsClientView


T = TypeVar("T", bound="ZpodNfsExportView")


@_attrs_define
class ZpodNfsExportView:
    """
    Attributes:
        active (bool):
        clients (list[ZpodNfsClientView]):
        options (str):
        owner (str):
        path (str):
        protected (bool):
        folder (None | str | Unset):
        folder_exists (bool | Unset):  Default: True.
        storage (None | str | Unset):
    """

    active: bool
    clients: list[ZpodNfsClientView]
    options: str
    owner: str
    path: str
    protected: bool
    folder: None | str | Unset = UNSET
    folder_exists: bool | Unset = True
    storage: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active = self.active

        clients = []
        for clients_item_data in self.clients:
            clients_item = clients_item_data.to_dict()
            clients.append(clients_item)

        options = self.options

        owner = self.owner

        path = self.path

        protected = self.protected

        folder: None | str | Unset
        if isinstance(self.folder, Unset):
            folder = UNSET
        else:
            folder = self.folder

        folder_exists = self.folder_exists

        storage: None | str | Unset
        if isinstance(self.storage, Unset):
            storage = UNSET
        else:
            storage = self.storage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "active": active,
                "clients": clients,
                "options": options,
                "owner": owner,
                "path": path,
                "protected": protected,
            }
        )
        if folder is not UNSET:
            field_dict["folder"] = folder
        if folder_exists is not UNSET:
            field_dict["folder_exists"] = folder_exists
        if storage is not UNSET:
            field_dict["storage"] = storage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_nfs_client_view import ZpodNfsClientView

        d = dict(src_dict)
        active = d.pop("active")

        clients = []
        _clients = d.pop("clients")
        for clients_item_data in _clients:
            clients_item = ZpodNfsClientView.from_dict(clients_item_data)

            clients.append(clients_item)

        options = d.pop("options")

        owner = d.pop("owner")

        path = d.pop("path")

        protected = d.pop("protected")

        def _parse_folder(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        folder = _parse_folder(d.pop("folder", UNSET))

        folder_exists = d.pop("folder_exists", UNSET)

        def _parse_storage(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage = _parse_storage(d.pop("storage", UNSET))

        zpod_nfs_export_view = cls(
            active=active,
            clients=clients,
            options=options,
            owner=owner,
            path=path,
            protected=protected,
            folder=folder,
            folder_exists=folder_exists,
            storage=storage,
        )

        zpod_nfs_export_view.additional_properties = d
        return zpod_nfs_export_view

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
