from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="LibraryUpdate")


@attr.s(auto_attribs=True)
class LibraryUpdate:
    """
    Attributes:
        description (Union[Unset, str]):  Example: Default zPodFactory library.
        enabled (Union[Unset, bool]):
    """

    description: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        description = self.description
        enabled = self.enabled

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description", UNSET)

        enabled = d.pop("enabled", UNSET)

        library_update = cls(
            description=description,
            enabled=enabled,
        )

        return library_update
