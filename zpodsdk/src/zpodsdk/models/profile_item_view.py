from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileItemView")


@_attrs_define
class ProfileItemView:
    """
    Attributes:
        component_uid (str):
        host_id (int | None | Unset):
        hostname (None | str | Unset):
        vcpu (int | None | Unset):
        vdisks (list[int] | None | Unset):
        vmem (int | None | Unset):
        vnics (int | None | Unset):
    """

    component_uid: str
    host_id: int | None | Unset = UNSET
    hostname: None | str | Unset = UNSET
    vcpu: int | None | Unset = UNSET
    vdisks: list[int] | None | Unset = UNSET
    vmem: int | None | Unset = UNSET
    vnics: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        component_uid = self.component_uid

        host_id: int | None | Unset
        if isinstance(self.host_id, Unset):
            host_id = UNSET
        else:
            host_id = self.host_id

        hostname: None | str | Unset
        if isinstance(self.hostname, Unset):
            hostname = UNSET
        else:
            hostname = self.hostname

        vcpu: int | None | Unset
        if isinstance(self.vcpu, Unset):
            vcpu = UNSET
        else:
            vcpu = self.vcpu

        vdisks: list[int] | None | Unset
        if isinstance(self.vdisks, Unset):
            vdisks = UNSET
        elif isinstance(self.vdisks, list):
            vdisks = self.vdisks

        else:
            vdisks = self.vdisks

        vmem: int | None | Unset
        if isinstance(self.vmem, Unset):
            vmem = UNSET
        else:
            vmem = self.vmem

        vnics: int | None | Unset
        if isinstance(self.vnics, Unset):
            vnics = UNSET
        else:
            vnics = self.vnics

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "component_uid": component_uid,
            }
        )
        if host_id is not UNSET:
            field_dict["host_id"] = host_id
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if vcpu is not UNSET:
            field_dict["vcpu"] = vcpu
        if vdisks is not UNSET:
            field_dict["vdisks"] = vdisks
        if vmem is not UNSET:
            field_dict["vmem"] = vmem
        if vnics is not UNSET:
            field_dict["vnics"] = vnics

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        component_uid = d.pop("component_uid")

        def _parse_host_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_id = _parse_host_id(d.pop("host_id", UNSET))

        def _parse_hostname(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        hostname = _parse_hostname(d.pop("hostname", UNSET))

        def _parse_vcpu(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        vcpu = _parse_vcpu(d.pop("vcpu", UNSET))

        def _parse_vdisks(data: object) -> list[int] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                vdisks_type_0 = cast(list[int], data)

                return vdisks_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | None | Unset, data)

        vdisks = _parse_vdisks(d.pop("vdisks", UNSET))

        def _parse_vmem(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        vmem = _parse_vmem(d.pop("vmem", UNSET))

        def _parse_vnics(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        vnics = _parse_vnics(d.pop("vnics", UNSET))

        profile_item_view = cls(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vdisks=vdisks,
            vmem=vmem,
            vnics=vnics,
        )

        return profile_item_view
