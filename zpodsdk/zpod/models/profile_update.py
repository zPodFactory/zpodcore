from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
)

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_item_update import ProfileItemUpdate


T = TypeVar("T", bound="ProfileUpdate")


@attr.s(auto_attribs=True)
class ProfileUpdate:
    """
    Attributes:
        name (Union[Unset, str]):  Example: sddc.
        profile (Union[Unset, List[Union['ProfileItemUpdate', List['ProfileItemUpdate']]]]):
    """

    name: Union[Unset, str] = UNSET
    profile: Union[
        Unset, List[Union["ProfileItemUpdate", List["ProfileItemUpdate"]]]
    ] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.profile_item_update import ProfileItemUpdate

        name = self.name
        profile: Union[Unset, List[Union[Dict[str, Any], List[Dict[str, Any]]]]] = UNSET
        if not isinstance(self.profile, Unset):
            profile = []
            for profile_item_data in self.profile:
                profile_item: Union[Dict[str, Any], List[Dict[str, Any]]]

                if isinstance(profile_item_data, ProfileItemUpdate):
                    profile_item = profile_item_data.to_dict()

                else:
                    profile_item = []
                    for profile_item_type_1_item_data in profile_item_data:
                        profile_item_type_1_item = (
                            profile_item_type_1_item_data.to_dict()
                        )

                        profile_item.append(profile_item_type_1_item)

                profile.append(profile_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if profile is not UNSET:
            field_dict["profile"] = profile

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_item_update import ProfileItemUpdate

        d = src_dict.copy()
        name = d.pop("name", UNSET)

        profile = []
        _profile = d.pop("profile", UNSET)
        for profile_item_data in _profile or []:

            def _parse_profile_item(
                data: object
            ) -> Union["ProfileItemUpdate", List["ProfileItemUpdate"]]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    profile_item_type_0 = ProfileItemUpdate.from_dict(data)

                    return profile_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, list):
                    raise TypeError()
                profile_item_type_1 = []
                _profile_item_type_1 = data
                for profile_item_type_1_item_data in _profile_item_type_1:
                    profile_item_type_1_item = ProfileItemUpdate.from_dict(
                        profile_item_type_1_item_data
                    )

                    profile_item_type_1.append(profile_item_type_1_item)

                return profile_item_type_1

            profile_item = _parse_profile_item(profile_item_data)

            profile.append(profile_item)

        profile_update = cls(
            name=name,
            profile=profile,
        )

        return profile_update
