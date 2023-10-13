from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointPermissionGroupAddRemove")


@attr.s(auto_attribs=True)
class EndpointPermissionGroupAddRemove:
    """
    Attributes:
        group_id (Union[Unset, int]):  Example: 1.
        groupname (Union[Unset, str]):  Example: admins.
    """

    group_id: Union[Unset, int] = UNSET
    groupname: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        group_id = self.group_id
        groupname = self.groupname

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if groupname is not UNSET:
            field_dict["groupname"] = groupname

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        group_id = d.pop("group_id", UNSET)

        groupname = d.pop("groupname", UNSET)

        endpoint_permission_group_add_remove = cls(
            group_id=group_id,
            groupname=groupname,
        )

        return endpoint_permission_group_add_remove
