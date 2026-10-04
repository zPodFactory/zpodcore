from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserViewFullList")


@_attrs_define
class UserViewFullList:
    """
    Attributes:
        creation_date (datetime.datetime):
        description (str):
        email (str):
        id (int):
        status (str):
        superadmin (bool):
        username (str):
        api_token (None | str | Unset):
        last_connection_date (datetime.datetime | None | Unset):
    """

    creation_date: datetime.datetime
    description: str
    email: str
    id: int
    status: str
    superadmin: bool
    username: str
    api_token: None | str | Unset = UNSET
    last_connection_date: datetime.datetime | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description

        email = self.email

        id = self.id

        status = self.status

        superadmin = self.superadmin

        username = self.username

        api_token: None | str | Unset
        if isinstance(self.api_token, Unset):
            api_token = UNSET
        else:
            api_token = self.api_token

        last_connection_date: None | str | Unset
        if isinstance(self.last_connection_date, Unset):
            last_connection_date = UNSET
        elif isinstance(self.last_connection_date, datetime.datetime):
            last_connection_date = self.last_connection_date.isoformat()
        else:
            last_connection_date = self.last_connection_date

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "creation_date": creation_date,
                "description": description,
                "email": email,
                "id": id,
                "status": status,
                "superadmin": superadmin,
                "username": username,
            }
        )
        if api_token is not UNSET:
            field_dict["api_token"] = api_token
        if last_connection_date is not UNSET:
            field_dict["last_connection_date"] = last_connection_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        creation_date = datetime.datetime.fromisoformat(d.pop("creation_date"))

        description = d.pop("description")

        email = d.pop("email")

        id = d.pop("id")

        status = d.pop("status")

        superadmin = d.pop("superadmin")

        username = d.pop("username")

        def _parse_api_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_token = _parse_api_token(d.pop("api_token", UNSET))

        def _parse_last_connection_date(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_connection_date_type_0 = datetime.datetime.fromisoformat(data)

                return last_connection_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_connection_date = _parse_last_connection_date(
            d.pop("last_connection_date", UNSET)
        )

        user_view_full_list = cls(
            creation_date=creation_date,
            description=description,
            email=email,
            id=id,
            status=status,
            superadmin=superadmin,
            username=username,
            api_token=api_token,
            last_connection_date=last_connection_date,
        )

        return user_view_full_list
