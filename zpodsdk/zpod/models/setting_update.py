from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="SettingUpdate")


@attr.s(auto_attribs=True)
class SettingUpdate:
    """
    Attributes:
        description (Union[Unset, str]):  Example: default domain for every instances (zpodfactory.io).
        value (Union[Unset, str]):  Example: zpodfactory.io.
    """

    description: Union[Unset, str] = UNSET
    value: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description", UNSET)

        value = d.pop("value", UNSET)

        setting_update = cls(
            description=description,
            value=value,
        )

        return setting_update
