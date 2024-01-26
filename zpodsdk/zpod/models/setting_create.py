from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="SettingCreate")


@_attrs_define
class SettingCreate:
    """
    Attributes:
        description (str):
        name (str):
        value (str):
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
