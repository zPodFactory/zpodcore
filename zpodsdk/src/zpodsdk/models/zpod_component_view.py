from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
    cast,
)

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
        fqdn (Union[None, Unset, str]):
        hostname (Union[None, Unset, str]):
        ip (Union[None, Unset, str]):
        password (Union[None, Unset, str]):
        status (Union[Unset, str]):
        usernames (Union[List['ZpodComponentViewUsernamesType0Item'], None, Unset]):
        vcpu (Union[None, Unset, int]):
        vmem (Union[None, Unset, int]):
    """

    component: "ComponentView"
    fqdn: Union[None, Unset, str] = UNSET
    hostname: Union[None, Unset, str] = UNSET
    ip: Union[None, Unset, str] = UNSET
    password: Union[None, Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    usernames: Union[List["ZpodComponentViewUsernamesType0Item"], None, Unset] = UNSET
    vcpu: Union[None, Unset, int] = UNSET
    vmem: Union[None, Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        component = self.component.to_dict()

        fqdn: Union[None, Unset, str]
        if isinstance(self.fqdn, Unset):
            fqdn = UNSET
        else:
            fqdn = self.fqdn

        hostname: Union[None, Unset, str]
        if isinstance(self.hostname, Unset):
            hostname = UNSET
        else:
            hostname = self.hostname

        ip: Union[None, Unset, str]
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        password: Union[None, Unset, str]
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        status = self.status

        usernames: Union[List[Dict[str, Any]], None, Unset]
        if isinstance(self.usernames, Unset):
            usernames = UNSET
        elif isinstance(self.usernames, list):
            usernames = []
            for usernames_type_0_item_data in self.usernames:
                usernames_type_0_item = usernames_type_0_item_data.to_dict()
                usernames.append(usernames_type_0_item)

        else:
            usernames = self.usernames

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
        if vmem is not UNSET:
            field_dict["vmem"] = vmem

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.component_view import ComponentView
        from ..models.zpod_component_view_usernames_type_0_item import (
            ZpodComponentViewUsernamesType0Item,
        )

        d = src_dict.copy()
        component = ComponentView.from_dict(d.pop("component"))

        def _parse_fqdn(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        fqdn = _parse_fqdn(d.pop("fqdn", UNSET))

        def _parse_hostname(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        hostname = _parse_hostname(d.pop("hostname", UNSET))

        def _parse_ip(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ip = _parse_ip(d.pop("ip", UNSET))

        def _parse_password(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        password = _parse_password(d.pop("password", UNSET))

        status = d.pop("status", UNSET)

        def _parse_usernames(
            data: object,
        ) -> Union[List["ZpodComponentViewUsernamesType0Item"], None, Unset]:
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
            except:  # noqa: E722
                pass
            return cast(
                Union[List["ZpodComponentViewUsernamesType0Item"], None, Unset], data
            )

        usernames = _parse_usernames(d.pop("usernames", UNSET))

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

        zpod_component_view = cls(
            component=component,
            fqdn=fqdn,
            hostname=hostname,
            ip=ip,
            password=password,
            status=status,
            usernames=usernames,
            vcpu=vcpu,
            vmem=vmem,
        )

        return zpod_component_view
