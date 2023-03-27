import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

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
        enabled (bool):
        git_url (str):  Example: https://github.com/zpodfactory/zpodlibrary.
        name (str):  Example: default.
        last_modified_date (Union[Unset, None, datetime.datetime]):  Example: 2023-01-01T00:01:00.
    """

    creation_date: datetime.datetime
    description: str
    enabled: bool
    git_url: str
    name: str
    last_modified_date: Union[Unset, None, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description
        enabled = self.enabled
        git_url = self.git_url
        name = self.name
        last_modified_date: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_modified_date, Unset):
            last_modified_date = (
                self.last_modified_date.isoformat() if self.last_modified_date else None
            )

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "creation_date": creation_date,
                "description": description,
                "enabled": enabled,
                "git_url": git_url,
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

        name = d.pop("name")

        _last_modified_date = d.pop("last_modified_date", UNSET)
        last_modified_date: Union[Unset, None, datetime.datetime]
        if _last_modified_date is None:
            last_modified_date = None
        elif isinstance(_last_modified_date, Unset):
            last_modified_date = UNSET
        else:
            last_modified_date = isoparse(_last_modified_date)

        library_view = cls(
            creation_date=creation_date,
            description=description,
            enabled=enabled,
            git_url=git_url,
            name=name,
            last_modified_date=last_modified_date,
        )

        library_view.additional_properties = d
        return library_view

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
