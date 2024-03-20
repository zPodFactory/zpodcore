from typing import Any, Dict, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointNetworkUpdate")


@_attrs_define
class EndpointNetworkUpdate:
    """
    Attributes:
        password (Union[None, Unset, str]):
        username (Union[None, Unset, str]):
    """

    password: Union[None, Unset, str] = UNSET
    username: Union[None, Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        password: Union[None, Unset, str]
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        username: Union[None, Unset, str]
        if isinstance(self.username, Unset):
            username = UNSET
        else:
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

        def _parse_password(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_username(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        username = _parse_username(d.pop("username", UNSET))

        endpoint_network_update = cls(
            password=password,
            username=username,
        )

        return endpoint_network_update
