from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointComputeUpdate")


@_attrs_define
class EndpointComputeUpdate:
    """
    Attributes:
        password (None | str | Unset):
        username (None | str | Unset):
        vds (None | str | Unset):
    """

    password: None | str | Unset = UNSET
    username: None | str | Unset = UNSET
    vds: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        password: None | str | Unset
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        username: None | str | Unset
        if isinstance(self.username, Unset):
            username = UNSET
        else:
            username = self.username

        vds: None | str | Unset
        if isinstance(self.vds, Unset):
            vds = UNSET
        else:
            vds = self.vds

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if password is not UNSET:
            field_dict["password"] = password
        if username is not UNSET:
            field_dict["username"] = username
        if vds is not UNSET:
            field_dict["vds"] = vds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        username = _parse_username(d.pop("username", UNSET))

        def _parse_vds(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        vds = _parse_vds(d.pop("vds", UNSET))

        endpoint_compute_update = cls(
            password=password,
            username=username,
            vds=vds,
        )

        return endpoint_compute_update
