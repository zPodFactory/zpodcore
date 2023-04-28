from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="SettingCreate")


@attr.s(auto_attribs=True)
class SettingCreate:
    """
    Attributes:
        description (str):  Example: default domain for every instances (zpodfactory.io).
        name (str):  Example: default.
        value (str):  Example: zpodfactory.io.
    """

    description: str
    name: str
    value: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        name = self.name
        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "name": name,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        name = d.pop("name")

        value = d.pop("value")

        setting_create = cls(
            description=description,
            name=name,
            value=value,
        )

        return setting_create
