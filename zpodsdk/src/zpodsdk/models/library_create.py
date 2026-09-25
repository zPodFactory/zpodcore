from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="LibraryCreate")


@_attrs_define
class LibraryCreate:
    """
    Attributes:
        description (str):
        git_url (str):
        name (str):
    """

    description: str
    git_url: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        git_url = self.git_url

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "description": description,
                "git_url": git_url,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description")

        git_url = d.pop("git_url")

        name = d.pop("name")

        library_create = cls(
            description=description,
            git_url=git_url,
            name=name,
        )

        return library_create
