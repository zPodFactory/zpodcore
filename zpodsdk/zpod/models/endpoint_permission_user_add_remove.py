from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointPermissionUserAddRemove")


@attr.s(auto_attribs=True)
class EndpointPermissionUserAddRemove:
    """
    Attributes:
        user_id (Union[Unset, int]):  Example: 1.
        username (Union[Unset, str]):  Example: jdoe.
    """

    user_id: Union[Unset, int] = UNSET
    username: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        user_id = self.user_id
        username = self.username

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if username is not UNSET:
            field_dict["username"] = username

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id", UNSET)

        username = d.pop("username", UNSET)

        endpoint_permission_user_add_remove = cls(
            user_id=user_id,
            username=username,
        )

        return endpoint_permission_user_add_remove
