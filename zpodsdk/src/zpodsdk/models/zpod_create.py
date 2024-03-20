from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ZpodCreate")


@_attrs_define
class ZpodCreate:
    """
    Attributes:
        endpoint_id (int):
        name (str):
        profile (str):
        description (Union[Unset, str]):  Default: ''.
        domain (Union[Unset, str]):  Default: ''.
        enet_name (Union[None, Unset, str]):
    """

    endpoint_id: int
    name: str
    profile: str
    description: Union[Unset, str] = ""
    domain: Union[Unset, str] = ""
    enet_name: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        endpoint_id = self.endpoint_id

        name = self.name

        profile = self.profile

        description = self.description

        domain = self.domain

        enet_name: Union[None, Unset, str]
        if isinstance(self.enet_name, Unset):
            enet_name = UNSET
        else:
            enet_name = self.enet_name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "endpoint_id": endpoint_id,
                "name": name,
                "profile": profile,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if domain is not UNSET:
            field_dict["domain"] = domain
        if enet_name is not UNSET:
            field_dict["enet_name"] = enet_name

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        endpoint_id = d.pop("endpoint_id")

        name = d.pop("name")

        profile = d.pop("profile")

        description = d.pop("description", UNSET)

        domain = d.pop("domain", UNSET)

        def _parse_enet_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        enet_name = _parse_enet_name(d.pop("enet_name", UNSET))

        zpod_create = cls(
            endpoint_id=endpoint_id,
            name=name,
            profile=profile,
            description=description,
            domain=domain,
            enet_name=enet_name,
        )

        return zpod_create
