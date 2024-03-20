from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodComponentCreate")


@_attrs_define
class ZpodComponentCreate:
    """
    Attributes:
        component_uid (str):
        host_id (Union[None, Unset, int]):
        hostname (Union[None, Unset, str]):
        vcpu (Union[None, Unset, int]):
        vmem (Union[None, Unset, int]):
    """

    component_uid: str
    host_id: Union[None, Unset, int] = UNSET
    hostname: Union[None, Unset, str] = UNSET
    vcpu: Union[None, Unset, int] = UNSET
    vmem: Union[None, Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        component_uid = self.component_uid

        host_id: Union[None, Unset, int]
        if isinstance(self.host_id, Unset):
            host_id = UNSET
        else:
            host_id = self.host_id

        hostname: Union[None, Unset, str]
        if isinstance(self.hostname, Unset):
            hostname = UNSET
        else:
            hostname = self.hostname

        vcpu: Union[None, Unset, int]
        if isinstance(self.vcpu, Unset):
            vcpu = UNSET
        else:
            vcpu = self.vcpu

        vmem: Union[None, Unset, int]
        if isinstance(self.vmem, Unset):
            vmem = UNSET
        else:
            vmem = self.vmem

        field_dict: Dict[str, Any] = {}
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
        if vmem is not UNSET:
            field_dict["vmem"] = vmem

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_uid = d.pop("component_uid")

        def _parse_host_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        host_id = _parse_host_id(d.pop("host_id", UNSET))

        def _parse_hostname(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        hostname = _parse_hostname(d.pop("hostname", UNSET))

        def _parse_vcpu(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        vcpu = _parse_vcpu(d.pop("vcpu", UNSET))

        def _parse_vmem(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        vmem = _parse_vmem(d.pop("vmem", UNSET))

        zpod_component_create = cls(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vmem=vmem,
        )

        return zpod_component_create
