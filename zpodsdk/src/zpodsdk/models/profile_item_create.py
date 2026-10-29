from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.component_network_spec import ComponentNetworkSpec


T = TypeVar("T", bound="ProfileItemCreate")


@_attrs_define
class ProfileItemCreate:
    """
    Attributes:
        component_uid (str):
        host_id (int | None | Unset):
        hostname (None | str | Unset):
        nested (bool | None | Unset): Deploy nested in the zPod (true) or on the endpoint (false). Default: the
            component's component_isnested.
        network (ComponentNetworkSpec | None | Unset): Nested components only: the network to deploy with. Every field
            is optional; left out, the zPod's defaults apply.
        vcpu (int | None | Unset):
        vdisks (list[int] | None | Unset):
        vlan_id (int | None | Unset): Put the component on the zPod network with this VLAN, its interface tagged (ESXi).
            host_id is the last octet in that network's /24.
        vmem (int | None | Unset):
        vnics (int | None | Unset):
    """

    component_uid: str
    host_id: int | None | Unset = UNSET
    hostname: None | str | Unset = UNSET
    nested: bool | None | Unset = UNSET
    network: ComponentNetworkSpec | None | Unset = UNSET
    vcpu: int | None | Unset = UNSET
    vdisks: list[int] | None | Unset = UNSET
    vlan_id: int | None | Unset = UNSET
    vmem: int | None | Unset = UNSET
    vnics: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.component_network_spec import ComponentNetworkSpec

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

        nested: bool | None | Unset
        if isinstance(self.nested, Unset):
            nested = UNSET
        else:
            nested = self.nested

        network: dict[str, Any] | None | Unset
        if isinstance(self.network, Unset):
            network = UNSET
        elif isinstance(self.network, ComponentNetworkSpec):
            network = self.network.to_dict()
        else:
            network = self.network

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

        vlan_id: int | None | Unset
        if isinstance(self.vlan_id, Unset):
            vlan_id = UNSET
        else:
            vlan_id = self.vlan_id

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
        if nested is not UNSET:
            field_dict["nested"] = nested
        if network is not UNSET:
            field_dict["network"] = network
        if vcpu is not UNSET:
            field_dict["vcpu"] = vcpu
        if vdisks is not UNSET:
            field_dict["vdisks"] = vdisks
        if vlan_id is not UNSET:
            field_dict["vlan_id"] = vlan_id
        if vmem is not UNSET:
            field_dict["vmem"] = vmem
        if vnics is not UNSET:
            field_dict["vnics"] = vnics

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.component_network_spec import ComponentNetworkSpec

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

        def _parse_nested(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        nested = _parse_nested(d.pop("nested", UNSET))

        def _parse_network(data: object) -> ComponentNetworkSpec | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                network_type_0 = ComponentNetworkSpec.from_dict(data)

                return network_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ComponentNetworkSpec | None | Unset, data)

        network = _parse_network(d.pop("network", UNSET))

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

        def _parse_vlan_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        vlan_id = _parse_vlan_id(d.pop("vlan_id", UNSET))

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

        profile_item_create = cls(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            nested=nested,
            network=network,
            vcpu=vcpu,
            vdisks=vdisks,
            vlan_id=vlan_id,
            vmem=vmem,
            vnics=vnics,
        )

        return profile_item_create
