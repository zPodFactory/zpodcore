from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceCreate")


@attr.s(auto_attribs=True)
class InstanceCreate:
    """
    Attributes:
        domain (str):  Example: tanzu-lab.maindomain.com.
        endpoint_id (int):  Example: 1.
        name (str):  Example: tanzu-lab.
        profile (str):  Example: sddc-profile.
        description (Union[Unset, str]):  Default: ''. Example: Tanzu Lab zPod.
    """

    domain: str
    endpoint_id: int
    name: str
    profile: str
    description: Union[Unset, str] = ""

    def to_dict(self) -> Dict[str, Any]:
        domain = self.domain
        endpoint_id = self.endpoint_id
        name = self.name
        profile = self.profile
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "domain": domain,
                "endpoint_id": endpoint_id,
                "name": name,
                "profile": profile,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        domain = d.pop("domain")

        endpoint_id = d.pop("endpoint_id")

        name = d.pop("name")

        profile = d.pop("profile")

        description = d.pop("description", UNSET)

        instance_create = cls(
            domain=domain,
            endpoint_id=endpoint_id,
            name=name,
            profile=profile,
            description=description,
        )

        return instance_create
