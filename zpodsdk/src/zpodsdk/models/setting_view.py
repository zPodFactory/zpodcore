from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="SettingView")


@_attrs_define
class SettingView:
    """
    Attributes:
        description (str):
        id (int):
        name (str):
        value (str):
    """

    description: str
    id: int
    name: str
    value: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        id = self.id

        name = self.name

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "id": id,
                "name": name,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        id = d.pop("id")

        name = d.pop("name")

        value = d.pop("value")

        setting_view = cls(
            description=description,
            id=id,
            name=name,
            value=value,
        )

        return setting_view
