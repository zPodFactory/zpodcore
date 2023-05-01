from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceCreate")


@attr.s(auto_attribs=True)
class InstanceCreate:
    """
    Attributes:
        endpoint_id (int):  Example: 1.
        name (str):  Example: demo.
        profile (str):  Example: sddc.
        description (Union[Unset, str]):  Default: ''. Example: Demo zPod.
        domain (Union[Unset, str]):  Default: ''. Example: demo.maindomain.com.
    """

    endpoint_id: int
    name: str
    profile: str
    description: Union[Unset, str] = ""
    domain: Union[Unset, str] = ""

    def to_dict(self) -> Dict[str, Any]:
        endpoint_id = self.endpoint_id
        name = self.name
        profile = self.profile
        description = self.description
        domain = self.domain

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

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        endpoint_id = d.pop("endpoint_id")

        name = d.pop("name")

        profile = d.pop("profile")

        description = d.pop("description", UNSET)

        domain = d.pop("domain", UNSET)

        instance_create = cls(
            endpoint_id=endpoint_id,
            name=name,
            profile=profile,
            description=description,
            domain=domain,
        )

        return instance_create
