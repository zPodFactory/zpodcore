from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0


T = TypeVar("T", bound="ZpodUpdate")


@_attrs_define
class ZpodUpdate:
    """
    Attributes:
        description (None | str | Unset):
        features (None | Unset | ZpodUpdateFeaturesType0):
    """

    description: None | str | Unset = UNSET
    features: None | Unset | ZpodUpdateFeaturesType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        features: dict[str, Any] | None | Unset
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, ZpodUpdateFeaturesType0):
            features = self.features.to_dict()
        else:
            features = self.features

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if features is not UNSET:
            field_dict["features"] = features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.zpod_update_features_type_0 import ZpodUpdateFeaturesType0

        d = dict(src_dict)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_features(data: object) -> None | Unset | ZpodUpdateFeaturesType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_0 = ZpodUpdateFeaturesType0.from_dict(data)

                return features_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodUpdateFeaturesType0, data)

        features = _parse_features(d.pop("features", UNSET))

        zpod_update = cls(
            description=description,
            features=features,
        )

        return zpod_update
