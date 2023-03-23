import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserViewFull")


@attr.s(auto_attribs=True)
class UserViewFull:
    """
    Attributes:
        api_token (str):
        creation_date (datetime.datetime):  Example: 2023-01-01T00:00:00.
        description (str):  Example: Sample User.
        email (str):  Example: jdoe@example.com.
        id (int):  Example: 1.
        ssh_key (str):
        superadmin (bool):
        username (str):  Example: jdoe.
        last_connection_date (Union[Unset, None, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    api_token: str
    creation_date: datetime.datetime
    description: str
    email: str
    id: int
    ssh_key: str
    superadmin: bool
    username: str
    last_connection_date: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        api_token = self.api_token
        creation_date = self.creation_date.isoformat()

        description = self.description
        email = self.email
        id = self.id
        ssh_key = self.ssh_key
        superadmin = self.superadmin
        username = self.username
        last_connection_date: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_connection_date, Unset):
            last_connection_date = (
                self.last_connection_date.isoformat()
                if self.last_connection_date
                else None
            )

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_token": api_token,
                "creation_date": creation_date,
                "description": description,
                "email": email,
                "id": id,
                "ssh_key": ssh_key,
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
        api_token = d.pop("api_token")

        creation_date = isoparse(d.pop("creation_date"))

        description = d.pop("description")

        email = d.pop("email")

        id = d.pop("id")

        ssh_key = d.pop("ssh_key")

        superadmin = d.pop("superadmin")

        username = d.pop("username")

        _last_connection_date = d.pop("last_connection_date", UNSET)
        last_connection_date: Union[Unset, None, datetime.datetime]
        if _last_connection_date is None:
            last_connection_date = None
        elif isinstance(_last_connection_date, Unset):
            last_connection_date = UNSET
        else:
            last_connection_date = isoparse(_last_connection_date)

        user_view_full = cls(
            api_token=api_token,
            creation_date=creation_date,
            description=description,
            email=email,
            id=id,
            ssh_key=ssh_key,
            superadmin=superadmin,
            username=username,
            last_connection_date=last_connection_date,
        )

        user_view_full.additional_properties = d
        return user_view_full

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
