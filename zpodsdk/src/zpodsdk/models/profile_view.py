from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.profile_item_view import ProfileItemView


T = TypeVar("T", bound="ProfileView")


@_attrs_define
class ProfileView:
    """
    Attributes:
        creation_date (datetime.datetime):
        id (int):
        last_modified_date (datetime.datetime):
        name (str):
        profile (list[list[ProfileItemView] | ProfileItemView]):
    """

    creation_date: datetime.datetime
    id: int
    last_modified_date: datetime.datetime
    name: str
    profile: list[list[ProfileItemView] | ProfileItemView]

    def to_dict(self) -> dict[str, Any]:
        from ..models.profile_item_view import ProfileItemView

        creation_date = self.creation_date.isoformat()

        id = self.id

        last_modified_date = self.last_modified_date.isoformat()

        name = self.name

        profile = []
        for profile_item_data in self.profile:
            profile_item: dict[str, Any] | list[dict[str, Any]]
            if isinstance(profile_item_data, ProfileItemView):
                profile_item = profile_item_data.to_dict()
            else:
                profile_item = []
                for profile_item_type_1_item_data in profile_item_data:
                    profile_item_type_1_item = profile_item_type_1_item_data.to_dict()
                    profile_item.append(profile_item_type_1_item)

            profile.append(profile_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "creation_date": creation_date,
                "id": id,
                "last_modified_date": last_modified_date,
                "name": name,
                "profile": profile,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.profile_item_view import ProfileItemView

        d = dict(src_dict)
        creation_date = datetime.datetime.fromisoformat(d.pop("creation_date"))

        id = d.pop("id")

        last_modified_date = datetime.datetime.fromisoformat(
            d.pop("last_modified_date")
        )

        name = d.pop("name")

        profile = []
        _profile = d.pop("profile")
        for profile_item_data in _profile:

            def _parse_profile_item(
                data: object,
            ) -> list[ProfileItemView] | ProfileItemView:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    profile_item_type_0 = ProfileItemView.from_dict(data)

                    return profile_item_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, list):
                    raise TypeError()
                profile_item_type_1 = []
                _profile_item_type_1 = data
                for profile_item_type_1_item_data in _profile_item_type_1:
                    profile_item_type_1_item = ProfileItemView.from_dict(
                        profile_item_type_1_item_data
                    )

                    profile_item_type_1.append(profile_item_type_1_item)

                return profile_item_type_1

            profile_item = _parse_profile_item(profile_item_data)

            profile.append(profile_item)

        profile_view = cls(
            creation_date=creation_date,
            id=id,
            last_modified_date=last_modified_date,
            name=name,
            profile=profile,
        )

        return profile_view
