from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="EndpointView")


@_attrs_define
class EndpointView:
    """
    Attributes:
        description (str):
        enabled (bool):
        id (int):
        name (str):
    """

    description: str
    enabled: bool
    id: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        enabled = self.enabled

        id = self.id

        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "enabled": enabled,
                "id": id,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        enabled = d.pop("enabled")

        id = d.pop("id")

        name = d.pop("name")

        endpoint_view = cls(
            description=description,
            enabled=enabled,
            id=id,
            name=name,
        )

        return endpoint_view
