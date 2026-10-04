from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="LibraryView")


@_attrs_define
class LibraryView:
    """
    Attributes:
        creation_date (datetime.datetime):
        description (str):
        enabled (bool):
        git_url (str):
        id (int):
        name (str):
        last_modified_date (datetime.datetime | None | Unset):
    """

    creation_date: datetime.datetime
    description: str
    enabled: bool
    git_url: str
    id: int
    name: str
    last_modified_date: datetime.datetime | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description

        enabled = self.enabled

        git_url = self.git_url

        id = self.id

        name = self.name

        last_modified_date: None | str | Unset
        if isinstance(self.last_modified_date, Unset):
            last_modified_date = UNSET
        elif isinstance(self.last_modified_date, datetime.datetime):
            last_modified_date = self.last_modified_date.isoformat()
        else:
            last_modified_date = self.last_modified_date

        field_dict: dict[str, Any] = {}

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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        creation_date = datetime.datetime.fromisoformat(d.pop("creation_date"))

        description = d.pop("description")

        enabled = d.pop("enabled")

        git_url = d.pop("git_url")

        id = d.pop("id")

        name = d.pop("name")

        def _parse_last_modified_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_modified_date_type_0 = datetime.datetime.fromisoformat(data)

                return last_modified_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_modified_date = _parse_last_modified_date(
            d.pop("last_modified_date", UNSET)
        )

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
