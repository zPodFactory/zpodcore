from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_disk_view import ZpodDiskView


T = TypeVar("T", bound="ZpodDiskRunView")


@_attrs_define
class ZpodDiskRunView:
    """
    Attributes:
        disk (None | Unset | ZpodDiskView):
        flow_run_id (None | str | Unset):
        message (None | str | Unset):
        name (None | str | Unset):
        state (str | Unset):  Default: 'SCHEDULED'.
    """

    disk: None | Unset | ZpodDiskView = UNSET
    flow_run_id: None | str | Unset = UNSET
    message: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    state: str | Unset = "SCHEDULED"

    def to_dict(self) -> dict[str, Any]:
        from ..models.zpod_disk_view import ZpodDiskView

        disk: dict[str, Any] | None | Unset
        if isinstance(self.disk, Unset):
            disk = UNSET
        elif isinstance(self.disk, ZpodDiskView):
            disk = self.disk.to_dict()
        else:
            disk = self.disk

        flow_run_id: None | str | Unset
        if isinstance(self.flow_run_id, Unset):
            flow_run_id = UNSET
        else:
            flow_run_id = self.flow_run_id

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        state = self.state

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if disk is not UNSET:
            field_dict["disk"] = disk
        if flow_run_id is not UNSET:
            field_dict["flow_run_id"] = flow_run_id
        if message is not UNSET:
            field_dict["message"] = message
        if name is not UNSET:
            field_dict["name"] = name
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_disk_view import ZpodDiskView

        d = dict(src_dict)

        def _parse_disk(data: object) -> None | Unset | ZpodDiskView:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                disk_type_0 = ZpodDiskView.from_dict(data)

                return disk_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodDiskView, data)

        disk = _parse_disk(d.pop("disk", UNSET))

        def _parse_flow_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        flow_run_id = _parse_flow_run_id(d.pop("flow_run_id", UNSET))

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        state = d.pop("state", UNSET)

        zpod_disk_run_view = cls(
            disk=disk,
            flow_run_id=flow_run_id,
            message=message,
            name=name,
            state=state,
        )

        return zpod_disk_run_view
