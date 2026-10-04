from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

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

    def to_dict(self) -> dict[str, Any]:
        permission = self.permission.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "permission": permission,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        permission = ZpodPermission(d.pop("permission"))

        zpod_permission_mine_view = cls(
            permission=permission,
        )

        return zpod_permission_mine_view
