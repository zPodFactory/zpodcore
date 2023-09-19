from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="PermissionGroupCreate")


@attr.s(auto_attribs=True)
class PermissionGroupCreate:
    """
    Attributes:
        name (str):  Example: Team.
    """

    name: str

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        permission_group_create = cls(
            name=name,
        )

        return permission_group_create
