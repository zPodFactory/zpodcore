from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Type,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0


T = TypeVar("T", bound="ZpodUpdate")


@_attrs_define
class ZpodUpdate:
    """
    Attributes:
        description (Union[None, Unset, str]):
        features (Union['ZpodUpdateFeaturesType0', None, Unset]):
    """

    description: Union[None, Unset, str] = UNSET
    features: Union["ZpodUpdateFeaturesType0", None, Unset] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        features: Union[Dict[str, Any], None, Unset]
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, ZpodUpdateFeaturesType0):
            features = self.features.to_dict()
        else:
            features = self.features

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if features is not UNSET:
            field_dict["features"] = features

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0

        d = src_dict.copy()

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_features(
            data: object,
        ) -> Union["ZpodUpdateFeaturesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_0 = ZpodUpdateFeaturesType0.from_dict(data)

                return features_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ZpodUpdateFeaturesType0", None, Unset], data)

        features = _parse_features(d.pop("features", UNSET))

        zpod_update = cls(
            description=description,
            features=features,
        )

        return zpod_update
