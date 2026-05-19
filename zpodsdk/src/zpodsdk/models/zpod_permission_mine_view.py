from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

from ..models.zpod_permission import ZpodPermission

T = TypeVar("T", bound="ZpodPermissionMineView")


@_attrs_define
class ZpodPermissionMineView:
    """
    Attributes:
        permission (ZpodPermission):
    """

    permission: ZpodPermission

    def to_dict(self) -> Dict[str, Any]:
        permission = self.permission.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "permission": permission,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        permission = ZpodPermission(d.pop("permission"))

        zpod_permission_mine_view = cls(
            permission=permission,
        )

        return zpod_permission_mine_view
