from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceUpdate")


@attr.s(auto_attribs=True)
class InstanceUpdate:
    """
    Attributes:
        description (Union[Unset, str]):  Example: Tanzu Lab zPod.
        id (Union[Unset, int]):  Example: 1.
    """

    description: Union[Unset, str] = UNSET
    id: Union[Unset, int] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description", UNSET)

        id = d.pop("id", UNSET)

        instance_update = cls(
            description=description,
            id=id,
        )

        return instance_update
