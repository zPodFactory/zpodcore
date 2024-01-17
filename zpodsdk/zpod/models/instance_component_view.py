from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.component_view import ComponentView


T = TypeVar("T", bound="InstanceComponentView")


@attr.s(auto_attribs=True)
class InstanceComponentView:
    """
    Attributes:
        component (ComponentView):
        fqdn (Union[Unset, str]):  Example: esxi13.demo.zpodfactory.io.
        hostname (Union[Unset, str]):  Example: esxi13.
        ip (Union[Unset, str]):  Example: 10.196.176.13.
        status (Union[Unset, str]):  Example: ACTIVE.
        vcpu (Union[Unset, int]):  Example: 4.
        vmem (Union[Unset, int]):  Example: 16.
    """

    component: "ComponentView"
    fqdn: Union[Unset, str] = UNSET
    hostname: Union[Unset, str] = UNSET
    ip: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    vcpu: Union[Unset, int] = UNSET
    vmem: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        component = self.component.to_dict()

        fqdn = self.fqdn
        hostname = self.hostname
        ip = self.ip
        status = self.status
        vcpu = self.vcpu
        vmem = self.vmem

        field_dict: Dict[str, Any] = {}
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
        if status is not UNSET:
            field_dict["status"] = status
        if vcpu is not UNSET:
            field_dict["vcpu"] = vcpu
        if vmem is not UNSET:
            field_dict["vmem"] = vmem

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.component_view import ComponentView

        d = src_dict.copy()
        component = ComponentView.from_dict(d.pop("component"))

        fqdn = d.pop("fqdn", UNSET)

        hostname = d.pop("hostname", UNSET)

        ip = d.pop("ip", UNSET)

        status = d.pop("status", UNSET)

        vcpu = d.pop("vcpu", UNSET)

        vmem = d.pop("vmem", UNSET)

        instance_component_view = cls(
            component=component,
            fqdn=fqdn,
            hostname=hostname,
            ip=ip,
            status=status,
            vcpu=vcpu,
            vmem=vmem,
        )

        return instance_component_view
