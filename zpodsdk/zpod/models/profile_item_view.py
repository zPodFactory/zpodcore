from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProfileItemView")


@attr.s(auto_attribs=True)
class ProfileItemView:
    """
    Attributes:
        component_uid (str):  Example: zbox-11.7.
        host_id (Union[Unset, int]):  Example: 11.
        hostname (Union[Unset, str]):  Example: zbox.
        vcpu (Union[Unset, int]):  Example: 4.
        vmem (Union[Unset, int]):  Example: 12.
    """

    component_uid: str
    host_id: Union[Unset, int] = UNSET
    hostname: Union[Unset, str] = UNSET
    vcpu: Union[Unset, int] = UNSET
    vmem: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        component_uid = self.component_uid
        host_id = self.host_id
        hostname = self.hostname
        vcpu = self.vcpu
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

        host_id = d.pop("host_id", UNSET)

        hostname = d.pop("hostname", UNSET)

        vcpu = d.pop("vcpu", UNSET)

        vmem = d.pop("vmem", UNSET)

        profile_item_view = cls(
            component_uid=component_uid,
            host_id=host_id,
            hostname=hostname,
            vcpu=vcpu,
            vmem=vmem,
        )

        return profile_item_view
