from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="ComponentUpdate")


@attr.s(auto_attribs=True)
class ComponentUpdate:
    """
    Attributes:
        enabled (bool):  Example: True.
    """

    enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        enabled = self.enabled

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "enabled": enabled,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        enabled = d.pop("enabled")

        component_update = cls(
            enabled=enabled,
        )

        return component_update
