from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PermissionGroupUserAdd")


@_attrs_define
class PermissionGroupUserAdd:
    """
    Attributes:
        user_id (int):
    """

    user_id: int

    def to_dict(self) -> Dict[str, Any]:
        user_id = self.user_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "user_id": user_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        permission_group_user_add = cls(
            user_id=user_id,
        )

        return permission_group_user_add
