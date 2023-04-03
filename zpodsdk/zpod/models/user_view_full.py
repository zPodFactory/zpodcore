import datetime
from typing import Any, Dict, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserViewFull")


@attr.s(auto_attribs=True)
class UserViewFull:
    """
    Attributes:
        creation_date (datetime.datetime):  Example: 2023-01-01T00:00:00.
        description (str):  Example: Sample User.
        email (str):  Example: jdoe@example.com.
        id (int):  Example: 1.
        superadmin (bool):
        username (str):  Example: jdoe.
        last_connection_date (Union[Unset, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    creation_date: datetime.datetime
    description: str
    email: str
    id: int
    superadmin: bool
    username: str
    last_connection_date: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description
        email = self.email
        id = self.id
        superadmin = self.superadmin
        username = self.username
        last_connection_date: Union[Unset, str] = UNSET
        if not isinstance(self.last_connection_date, Unset):
            last_connection_date = self.last_connection_date.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "creation_date": creation_date,
                "description": description,
                "email": email,
                "id": id,
                "superadmin": superadmin,
                "username": username,
            }
        )
        if last_connection_date is not UNSET:
            field_dict["last_connection_date"] = last_connection_date

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        creation_date = isoparse(d.pop("creation_date"))

        description = d.pop("description")

        email = d.pop("email")

        id = d.pop("id")

        superadmin = d.pop("superadmin")

        username = d.pop("username")

        _last_connection_date = d.pop("last_connection_date", UNSET)
        last_connection_date: Union[Unset, datetime.datetime]
        if isinstance(_last_connection_date, Unset):
            last_connection_date = UNSET
        else:
            last_connection_date = isoparse(_last_connection_date)

        user_view_full = cls(
            creation_date=creation_date,
            description=description,
            email=email,
            id=id,
            superadmin=superadmin,
            username=username,
            last_connection_date=last_connection_date,
        )

        return user_view_full
