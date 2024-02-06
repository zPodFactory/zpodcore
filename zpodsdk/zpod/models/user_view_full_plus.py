import datetime
from typing import (
    Any,
    Dict,
    Type,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserViewFullPlus")


@_attrs_define
class UserViewFullPlus:
    """
    Attributes:
        api_token (str):
        creation_date (datetime.datetime):
        description (str):
        email (str):
        id (int):
        status (str):
        superadmin (bool):
        username (str):
        last_connection_date (Union[None, Unset, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    api_token: str
    creation_date: datetime.datetime
    description: str
    email: str
    id: int
    status: str
    superadmin: bool
    username: str
    last_connection_date: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        api_token = self.api_token

        creation_date = self.creation_date.isoformat()

        description = self.description

        email = self.email

        id = self.id

        status = self.status

        superadmin = self.superadmin

        username = self.username

        last_connection_date: Union[None, Unset, str]
        if isinstance(self.last_connection_date, Unset):
            last_connection_date = UNSET
        elif isinstance(self.last_connection_date, datetime.datetime):
            last_connection_date = self.last_connection_date.isoformat()
        else:
            last_connection_date = self.last_connection_date

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "api_token": api_token,
                "creation_date": creation_date,
                "description": description,
                "email": email,
                "id": id,
                "status": status,
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

        status = d.pop("status")

        superadmin = d.pop("superadmin")

        username = d.pop("username")

        def _parse_last_connection_date(
            data: object,
        ) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_connection_date_type_0 = isoparse(data)

                return last_connection_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        last_connection_date = _parse_last_connection_date(
            d.pop("last_connection_date", UNSET)
        )

        user_view_full_plus = cls(
            api_token=api_token,
            creation_date=creation_date,
            description=description,
            email=email,
            id=id,
            status=status,
            superadmin=superadmin,
            username=username,
            last_connection_date=last_connection_date,
        )

        return user_view_full_plus
