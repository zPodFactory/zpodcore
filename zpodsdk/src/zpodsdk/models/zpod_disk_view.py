from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.zpod_disk_kind import ZpodDiskKind
from ..models.zpod_disk_status import ZpodDiskStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodDiskView")


@_attrs_define
class ZpodDiskView:
    """
    Attributes:
        kind (ZpodDiskKind):
        size_gb (int):
        status (ZpodDiskStatus):
        device (None | str | Unset):
        disk_uuid (None | str | Unset):
        id (int | None | Unset):
        scsi (None | str | Unset):
        state (None | str | Unset):
        storage (None | str | Unset):
    """

    kind: ZpodDiskKind
    size_gb: int
    status: ZpodDiskStatus
    device: None | str | Unset = UNSET
    disk_uuid: None | str | Unset = UNSET
    id: int | None | Unset = UNSET
    scsi: None | str | Unset = UNSET
    state: None | str | Unset = UNSET
    storage: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind.value

        size_gb = self.size_gb

        status = self.status.value

        device: None | str | Unset
        if isinstance(self.device, Unset):
            device = UNSET
        else:
            device = self.device

        disk_uuid: None | str | Unset
        if isinstance(self.disk_uuid, Unset):
            disk_uuid = UNSET
        else:
            disk_uuid = self.disk_uuid

        id: int | None | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        scsi: None | str | Unset
        if isinstance(self.scsi, Unset):
            scsi = UNSET
        else:
            scsi = self.scsi

        state: None | str | Unset
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        storage: None | str | Unset
        if isinstance(self.storage, Unset):
            storage = UNSET
        else:
            storage = self.storage

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "kind": kind,
                "size_gb": size_gb,
                "status": status,
            }
        )
        if device is not UNSET:
            field_dict["device"] = device
        if disk_uuid is not UNSET:
            field_dict["disk_uuid"] = disk_uuid
        if id is not UNSET:
            field_dict["id"] = id
        if scsi is not UNSET:
            field_dict["scsi"] = scsi
        if state is not UNSET:
            field_dict["state"] = state
        if storage is not UNSET:
            field_dict["storage"] = storage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = ZpodDiskKind(d.pop("kind"))

        size_gb = d.pop("size_gb")

        status = ZpodDiskStatus(d.pop("status"))

        def _parse_device(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        device = _parse_device(d.pop("device", UNSET))

        def _parse_disk_uuid(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        disk_uuid = _parse_disk_uuid(d.pop("disk_uuid", UNSET))

        def _parse_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_scsi(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        scsi = _parse_scsi(d.pop("scsi", UNSET))

        def _parse_state(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        state = _parse_state(d.pop("state", UNSET))

        def _parse_storage(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage = _parse_storage(d.pop("storage", UNSET))

        zpod_disk_view = cls(
            kind=kind,
            size_gb=size_gb,
            status=status,
            device=device,
            disk_uuid=disk_uuid,
            id=id,
            scsi=scsi,
            state=state,
            storage=storage,
        )

        return zpod_disk_view
