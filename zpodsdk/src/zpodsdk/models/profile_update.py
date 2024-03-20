from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.profile_item_update import ProfileItemUpdate


T = TypeVar("T", bound="ProfileUpdate")


@_attrs_define
class ProfileUpdate:
    """
    Attributes:
        name (Union[None, Unset, str]):
        profile (Union[List[Union['ProfileItemUpdate', List['ProfileItemUpdate']]], None, Unset]):
    """

    name: Union[None, Unset, str] = UNSET
    profile: Union[
        List[Union["ProfileItemUpdate", List["ProfileItemUpdate"]]], None, Unset
    ] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.profile_item_update import ProfileItemUpdate

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        profile: Union[List[Union[Dict[str, Any], List[Dict[str, Any]]]], None, Unset]
        if isinstance(self.profile, Unset):
            profile = UNSET
        elif isinstance(self.profile, list):
            profile = []
            for profile_type_0_item_data in self.profile:
                profile_type_0_item: Union[Dict[str, Any], List[Dict[str, Any]]]
                if isinstance(profile_type_0_item_data, ProfileItemUpdate):
                    profile_type_0_item = profile_type_0_item_data.to_dict()
                else:
                    profile_type_0_item = []
                    for (
                        profile_type_0_item_type_1_item_data
                    ) in profile_type_0_item_data:
                        profile_type_0_item_type_1_item = (
                            profile_type_0_item_type_1_item_data.to_dict()
                        )
                        profile_type_0_item.append(profile_type_0_item_type_1_item)

                profile.append(profile_type_0_item)

        else:
            profile = self.profile

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

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_profile(
            data: object,
        ) -> Union[
            List[Union["ProfileItemUpdate", List["ProfileItemUpdate"]]], None, Unset
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                profile_type_0 = []
                _profile_type_0 = data
                for profile_type_0_item_data in _profile_type_0:

                    def _parse_profile_type_0_item(
                        data: object,
                    ) -> Union["ProfileItemUpdate", List["ProfileItemUpdate"]]:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            profile_type_0_item_type_0 = ProfileItemUpdate.from_dict(
                                data
                            )

                            return profile_type_0_item_type_0
                        except:  # noqa: E722
                            pass
                        if not isinstance(data, list):
                            raise TypeError()
                        profile_type_0_item_type_1 = []
                        _profile_type_0_item_type_1 = data
                        for (
                            profile_type_0_item_type_1_item_data
                        ) in _profile_type_0_item_type_1:
                            profile_type_0_item_type_1_item = (
                                ProfileItemUpdate.from_dict(
                                    profile_type_0_item_type_1_item_data
                                )
                            )

                            profile_type_0_item_type_1.append(
                                profile_type_0_item_type_1_item
                            )

                        return profile_type_0_item_type_1

                    profile_type_0_item = _parse_profile_type_0_item(
                        profile_type_0_item_data
                    )

                    profile_type_0.append(profile_type_0_item)

                return profile_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    List[Union["ProfileItemUpdate", List["ProfileItemUpdate"]]],
                    None,
                    Unset,
                ],
                data,
            )

        profile = _parse_profile(d.pop("profile", UNSET))

        profile_update = cls(
            name=name,
            profile=profile,
        )

        return profile_update
