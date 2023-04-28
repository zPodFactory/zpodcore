from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstanceUpdate")


@attr.s(auto_attribs=True)
class InstanceUpdate:
    """
    Attributes:
        description (Union[Unset, str]):  Example: Demo zPod.
    """

    description: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description", UNSET)

        instance_update = cls(
            description=description,
        )

        return instance_update
