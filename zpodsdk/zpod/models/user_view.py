import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserView")


@attr.s(auto_attribs=True)
class UserView:
    """
    Attributes:
        api_token (str):
        creation_date (datetime.datetime):  Example: 2023-01-01T00:00:00.
        description (str):  Example: Sample User.
        email (str):  Example: jdoe@example.com.
        ssh_key (str):
        superadmin (bool):
        username (str):  Example: jdoe.
        last_connection (Union[Unset, None, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    api_token: str
    creation_date: datetime.datetime
    description: str
    email: str
    ssh_key: str
    superadmin: bool
    username: str
    last_connection: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        api_token = self.api_token
        creation_date = self.creation_date.isoformat()

        description = self.description
        email = self.email
        ssh_key = self.ssh_key
        superadmin = self.superadmin
        username = self.username
        last_connection: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_connection, Unset):
            last_connection = self.last_connection.isoformat() if self.last_connection else None

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_token": api_token,
                "creation_date": creation_date,
                "description": description,
                "email": email,
                "ssh_key": ssh_key,
                "superadmin": superadmin,
                "username": username,
            }
        )
        if last_connection is not UNSET:
            field_dict["last_connection"] = last_connection

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        api_token = d.pop("api_token")

        creation_date = isoparse(d.pop("creation_date"))

        description = d.pop("description")

        email = d.pop("email")

        ssh_key = d.pop("ssh_key")

        superadmin = d.pop("superadmin")

        username = d.pop("username")

        _last_connection = d.pop("last_connection", UNSET)
        last_connection: Union[Unset, None, datetime.datetime]
        if _last_connection is None:
            last_connection = None
        elif isinstance(_last_connection, Unset):
            last_connection = UNSET
        else:
            last_connection = isoparse(_last_connection)

        user_view = cls(
            api_token=api_token,
            creation_date=creation_date,
            description=description,
            email=email,
            ssh_key=ssh_key,
            superadmin=superadmin,
            username=username,
            last_connection=last_connection,
        )

        user_view.additional_properties = d
        return user_view

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
