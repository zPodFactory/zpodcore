from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="LibraryCreate")


@attr.s(auto_attribs=True)
class LibraryCreate:
    """
    Attributes:
        description (str):  Example: Default zPodFactory library.
        git_url (str):  Example: https://github.com/zpodfactory/zpodlibrary.
        name (str):  Example: vmware.
    """

    description: str
    git_url: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        git_url = self.git_url
        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "git_url": git_url,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        git_url = d.pop("git_url")

        name = d.pop("name")

        library_create = cls(
            description=description,
            git_url=git_url,
            name=name,
        )

        return library_create
