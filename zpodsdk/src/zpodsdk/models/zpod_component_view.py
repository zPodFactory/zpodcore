from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.component_view import ComponentView
    from ..models.zpod_component_view_usernames_type_0_item import (
        ZpodComponentViewUsernamesType0Item,
    )


T = TypeVar("T", bound="ZpodComponentView")


@_attrs_define
class ZpodComponentView:
    """
    Attributes:
        component (ComponentView):
        fqdn (None | str | Unset):
        hostname (None | str | Unset):
        ip (None | str | Unset):
        password (None | str | Unset):
        status (str | Unset):
        usernames (list[ZpodComponentViewUsernamesType0Item] | None | Unset):
        vcpu (int | None | Unset):
        vdisks (list[int] | None | Unset):
        vmem (int | None | Unset):
        vnics (int | None | Unset):
    """

    component: ComponentView
    fqdn: None | str | Unset = UNSET
    hostname: None | str | Unset = UNSET
    ip: None | str | Unset = UNSET
    password: None | str | Unset = UNSET
    status: str | Unset = UNSET
    usernames: list[ZpodComponentViewUsernamesType0Item] | None | Unset = UNSET
    vcpu: int | None | Unset = UNSET
    vdisks: list[int] | None | Unset = UNSET
    vmem: int | None | Unset = UNSET
    vnics: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        component = self.component.to_dict()

        fqdn: None | str | Unset
        if isinstance(self.fqdn, Unset):
            fqdn = UNSET
        else:
            fqdn = self.fqdn

        hostname: None | str | Unset
        if isinstance(self.hostname, Unset):
            hostname = UNSET
        else:
            hostname = self.hostname

        ip: None | str | Unset
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        password: None | str | Unset
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        status = self.status

        usernames: list[dict[str, Any]] | None | Unset
        if isinstance(self.usernames, Unset):
            usernames = UNSET
        elif isinstance(self.usernames, list):
            usernames = []
            for usernames_type_0_item_data in self.usernames:
                usernames_type_0_item = usernames_type_0_item_data.to_dict()
                usernames.append(usernames_type_0_item)

        else:
            usernames = self.usernames

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
                "component": component,
            }
        )
        if fqdn is not UNSET:
            field_dict["fqdn"] = fqdn
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if ip is not UNSET:
            field_dict["ip"] = ip
        if password is not UNSET:
            field_dict["password"] = password
        if status is not UNSET:
            field_dict["status"] = status
        if usernames is not UNSET:
            field_dict["usernames"] = usernames
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
        from ..models.component_view import ComponentView
        from ..models.zpod_component_view_usernames_type_0_item import (
            ZpodComponentViewUsernamesType0Item,
        )

        d = dict(src_dict)
        component = ComponentView.from_dict(d.pop("component"))

        def _parse_fqdn(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        fqdn = _parse_fqdn(d.pop("fqdn", UNSET))

        def _parse_hostname(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        hostname = _parse_hostname(d.pop("hostname", UNSET))

        def _parse_ip(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip = _parse_ip(d.pop("ip", UNSET))

        def _parse_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        password = _parse_password(d.pop("password", UNSET))

        status = d.pop("status", UNSET)

        def _parse_usernames(
            data: object,
        ) -> list[ZpodComponentViewUsernamesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                usernames_type_0 = []
                _usernames_type_0 = data
                for usernames_type_0_item_data in _usernames_type_0:
                    usernames_type_0_item = (
                        ZpodComponentViewUsernamesType0Item.from_dict(
                            usernames_type_0_item_data
                        )
                    )

                    usernames_type_0.append(usernames_type_0_item)

                return usernames_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ZpodComponentViewUsernamesType0Item] | None | Unset, data)

        usernames = _parse_usernames(d.pop("usernames", UNSET))

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

        zpod_component_view = cls(
            component=component,
            fqdn=fqdn,
            hostname=hostname,
            ip=ip,
            password=password,
            status=status,
            usernames=usernames,
            vcpu=vcpu,
            vdisks=vdisks,
            vmem=vmem,
            vnics=vnics,
        )

        return zpod_component_view
