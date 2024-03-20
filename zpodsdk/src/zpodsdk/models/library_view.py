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
        last_modified_date (Union[None, Unset, datetime.datetime]):
    """

    creation_date: datetime.datetime
    description: str
    enabled: bool
    git_url: str
    id: int
    name: str
    last_modified_date: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        creation_date = self.creation_date.isoformat()

        description = self.description

        enabled = self.enabled

        git_url = self.git_url

        id = self.id

        name = self.name

        last_modified_date: Union[None, Unset, str]
        if isinstance(self.last_modified_date, Unset):
            last_modified_date = UNSET
        elif isinstance(self.last_modified_date, datetime.datetime):
            last_modified_date = self.last_modified_date.isoformat()
        else:
            last_modified_date = self.last_modified_date

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

        def _parse_last_modified_date(
            data: object,
        ) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_modified_date_type_0 = isoparse(data)

                return last_modified_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

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
