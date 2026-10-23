from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.zpod_storage_kind import ZpodStorageKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_storage_folder_view import ZpodStorageFolderView


T = TypeVar("T", bound="ZpodStorageView")


@_attrs_define
class ZpodStorageView:
    """
    Attributes:
        available_bytes (int):
        device (str):
        disk (str):
        exports (int):
        layout (str):
        managed (bool):
        mountpoint (str):
        name (str):
        protected (bool):
        size_bytes (int):
        used_bytes (int):
        folders (list[ZpodStorageFolderView] | Unset):
        fstype (None | str | Unset):
        kind (ZpodStorageKind | Unset):
        lv (None | str | Unset):
        uuid (None | str | Unset):
        vg (None | str | Unset):
    """

    available_bytes: int
    device: str
    disk: str
    exports: int
    layout: str
    managed: bool
    mountpoint: str
    name: str
    protected: bool
    size_bytes: int
    used_bytes: int
    folders: list[ZpodStorageFolderView] | Unset = UNSET
    fstype: None | str | Unset = UNSET
    kind: ZpodStorageKind | Unset = UNSET
    lv: None | str | Unset = UNSET
    uuid: None | str | Unset = UNSET
    vg: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        available_bytes = self.available_bytes

        device = self.device

        disk = self.disk

        exports = self.exports

        layout = self.layout

        managed = self.managed

        mountpoint = self.mountpoint

        name = self.name

        protected = self.protected

        size_bytes = self.size_bytes

        used_bytes = self.used_bytes

        folders: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.folders, Unset):
            folders = []
            for folders_item_data in self.folders:
                folders_item = folders_item_data.to_dict()
                folders.append(folders_item)

        fstype: None | str | Unset
        if isinstance(self.fstype, Unset):
            fstype = UNSET
        else:
            fstype = self.fstype

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        lv: None | str | Unset
        if isinstance(self.lv, Unset):
            lv = UNSET
        else:
            lv = self.lv

        uuid: None | str | Unset
        if isinstance(self.uuid, Unset):
            uuid = UNSET
        else:
            uuid = self.uuid

        vg: None | str | Unset
        if isinstance(self.vg, Unset):
            vg = UNSET
        else:
            vg = self.vg

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "available_bytes": available_bytes,
                "device": device,
                "disk": disk,
                "exports": exports,
                "layout": layout,
                "managed": managed,
                "mountpoint": mountpoint,
                "name": name,
                "protected": protected,
                "size_bytes": size_bytes,
                "used_bytes": used_bytes,
            }
        )
        if folders is not UNSET:
            field_dict["folders"] = folders
        if fstype is not UNSET:
            field_dict["fstype"] = fstype
        if kind is not UNSET:
            field_dict["kind"] = kind
        if lv is not UNSET:
            field_dict["lv"] = lv
        if uuid is not UNSET:
            field_dict["uuid"] = uuid
        if vg is not UNSET:
            field_dict["vg"] = vg

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_storage_folder_view import ZpodStorageFolderView

        d = dict(src_dict)
        available_bytes = d.pop("available_bytes")

        device = d.pop("device")

        disk = d.pop("disk")

        exports = d.pop("exports")

        layout = d.pop("layout")

        managed = d.pop("managed")

        mountpoint = d.pop("mountpoint")

        name = d.pop("name")

        protected = d.pop("protected")

        size_bytes = d.pop("size_bytes")

        used_bytes = d.pop("used_bytes")

        _folders = d.pop("folders", UNSET)
        folders: list[ZpodStorageFolderView] | Unset = UNSET
        if _folders is not UNSET:
            folders = []
            for folders_item_data in _folders:
                folders_item = ZpodStorageFolderView.from_dict(folders_item_data)

                folders.append(folders_item)

        def _parse_fstype(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        fstype = _parse_fstype(d.pop("fstype", UNSET))

        _kind = d.pop("kind", UNSET)
        kind: ZpodStorageKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = ZpodStorageKind(_kind)

        def _parse_lv(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        lv = _parse_lv(d.pop("lv", UNSET))

        def _parse_uuid(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        uuid = _parse_uuid(d.pop("uuid", UNSET))

        def _parse_vg(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        vg = _parse_vg(d.pop("vg", UNSET))

        zpod_storage_view = cls(
            available_bytes=available_bytes,
            device=device,
            disk=disk,
            exports=exports,
            layout=layout,
            managed=managed,
            mountpoint=mountpoint,
            name=name,
            protected=protected,
            size_bytes=size_bytes,
            used_bytes=used_bytes,
            folders=folders,
            fstype=fstype,
            kind=kind,
            lv=lv,
            uuid=uuid,
            vg=vg,
        )

        zpod_storage_view.additional_properties = d
        return zpod_storage_view

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
