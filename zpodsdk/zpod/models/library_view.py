import datetime
from typing import Any, Dict, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="LibraryView")


@attr.s(auto_attribs=True)
class LibraryView:
    """
    Attributes:
        creation_date (datetime.datetime):  Example: 2023-01-01T00:00:00.
        description (str):  Example: Default zPodFactory library.
        enabled (bool):  Example: True.
        git_url (str):  Example: https://github.com/zpodfactory/zpodlibrary.
        id (str):  Example: 1.
        name (str):  Example: default.
        last_modified_date (Union[Unset, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    creation_date: datetime.datetime
    description: str
    enabled: bool
    git_url: str
    id: str
    name: str
    last_modified_date: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description
        enabled = self.enabled
        git_url = self.git_url
        id = self.id
        name = self.name
        last_modified_date: Union[Unset, str] = UNSET
        if not isinstance(self.last_modified_date, Unset):
            last_modified_date = self.last_modified_date.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "creation_date": creation_date,
                "description": description,
                "enabled": enabled,
                "git_url": git_url,
                "id": id,
                "name": name,
            }
        )
        if last_modified_date is not UNSET:
            field_dict["last_modified_date"] = last_modified_date

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        creation_date = isoparse(d.pop("creation_date"))

        description = d.pop("description")

        enabled = d.pop("enabled")

        git_url = d.pop("git_url")

        id = d.pop("id")

        name = d.pop("name")

        _last_modified_date = d.pop("last_modified_date", UNSET)
        last_modified_date: Union[Unset, datetime.datetime]
        if isinstance(_last_modified_date, Unset):
            last_modified_date = UNSET
        else:
            last_modified_date = isoparse(_last_modified_date)

        library_view = cls(
            creation_date=creation_date,
            description=description,
            enabled=enabled,
            git_url=git_url,
            id=id,
            name=name,
            last_modified_date=last_modified_date,
        )

        return library_view
