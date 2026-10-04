from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdate")


@_attrs_define
class UserUpdate:
    """
    Attributes:
        description (None | str | Unset):
        email (None | str | Unset):
        ssh_key (None | str | Unset):
    """

    description: None | str | Unset = UNSET
    email: None | str | Unset = UNSET
    ssh_key: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        ssh_key: None | str | Unset
        if isinstance(self.ssh_key, Unset):
            ssh_key = UNSET
        else:
            ssh_key = self.ssh_key

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if email is not UNSET:
            field_dict["email"] = email
        if ssh_key is not UNSET:
            field_dict["ssh_key"] = ssh_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_ssh_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ssh_key = _parse_ssh_key(d.pop("ssh_key", UNSET))

        user_update = cls(
            description=description,
            email=email,
            ssh_key=ssh_key,
        )

        return user_update
