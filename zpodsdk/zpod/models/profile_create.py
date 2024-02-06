from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.profile_item_create import ProfileItemCreate


T = TypeVar("T", bound="ProfileCreate")


@_attrs_define
class ProfileCreate:
    """
    Attributes:
        name (str):
        profile (List[Union['ProfileItemCreate', List['ProfileItemCreate']]]):
    """

    name: str
    profile: List[Union["ProfileItemCreate", List["ProfileItemCreate"]]]

    def to_dict(self) -> Dict[str, Any]:
        from ..models.profile_item_create import ProfileItemCreate

        name = self.name

        profile = []
        for profile_item_data in self.profile:
            profile_item: Union[Dict[str, Any], List[Dict[str, Any]]]
            if isinstance(profile_item_data, ProfileItemCreate):
                profile_item = profile_item_data.to_dict()
            else:
                profile_item = []
                for profile_item_type_1_item_data in profile_item_data:
                    profile_item_type_1_item = profile_item_type_1_item_data.to_dict()
                    profile_item.append(profile_item_type_1_item)

            profile.append(profile_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "profile": profile,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.profile_item_create import ProfileItemCreate

        d = src_dict.copy()
        name = d.pop("name")

        profile = []
        _profile = d.pop("profile")
        for profile_item_data in _profile:

            def _parse_profile_item(
                data: object,
            ) -> Union["ProfileItemCreate", List["ProfileItemCreate"]]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    profile_item_type_0 = ProfileItemCreate.from_dict(data)

                    return profile_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, list):
                    raise TypeError()
                profile_item_type_1 = []
                _profile_item_type_1 = data
                for profile_item_type_1_item_data in _profile_item_type_1:
                    profile_item_type_1_item = ProfileItemCreate.from_dict(
                        profile_item_type_1_item_data
                    )

                    profile_item_type_1.append(profile_item_type_1_item)

                return profile_item_type_1

            profile_item = _parse_profile_item(profile_item_data)

            profile.append(profile_item)

        profile_create = cls(
            name=name,
            profile=profile,
        )

        return profile_create
