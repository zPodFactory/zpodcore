from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointComputeUpdate")


@attr.s(auto_attribs=True)
class EndpointComputeUpdate:
    """
    Attributes:
        password (Union[Unset, str]):  Example: my-password.
        username (Union[Unset, str]):  Example: my-username.
    """

    password: Union[Unset, str] = UNSET
    username: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        password = self.password
        username = self.username

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if password is not UNSET:
            field_dict["password"] = password
        if username is not UNSET:
            field_dict["username"] = username

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        password = d.pop("password", UNSET)

        username = d.pop("username", UNSET)

        endpoint_compute_update = cls(
            password=password,
            username=username,
        )

        return endpoint_compute_update
