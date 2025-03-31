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
    from ..models.zpod_create_features_type_0 import ZpodCreateFeaturesType0


T = TypeVar("T", bound="ZpodCreate")


@_attrs_define
class ZpodCreate:
    """
    Attributes:
        endpoint_id (int):
        name (str):
        profile (str):
        description (Union[Unset, str]):  Default: ''.
        domain (Union[Unset, str]):  Default: ''.
        enet_name (Union[None, Unset, str]):
        features (Union['ZpodCreateFeaturesType0', None, Unset]):
    """

    endpoint_id: int
    name: str
    profile: str
    description: Union[Unset, str] = ""
    domain: Union[Unset, str] = ""
    enet_name: Union[None, Unset, str] = UNSET
    features: Union["ZpodCreateFeaturesType0", None, Unset] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.zpod_create_features_type_0 import ZpodCreateFeaturesType0

        endpoint_id = self.endpoint_id

        name = self.name

        profile = self.profile

        description = self.description

        domain = self.domain

        enet_name: Union[None, Unset, str]
        if isinstance(self.enet_name, Unset):
            enet_name = UNSET
        else:
            enet_name = self.enet_name

        features: Union[Dict[str, Any], None, Unset]
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, ZpodCreateFeaturesType0):
            features = self.features.to_dict()
        else:
            features = self.features

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "endpoint_id": endpoint_id,
                "name": name,
                "profile": profile,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if domain is not UNSET:
            field_dict["domain"] = domain
        if enet_name is not UNSET:
            field_dict["enet_name"] = enet_name
        if features is not UNSET:
            field_dict["features"] = features

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.zpod_create_features_type_0 import ZpodCreateFeaturesType0

        d = src_dict.copy()
        endpoint_id = d.pop("endpoint_id")

        name = d.pop("name")

        profile = d.pop("profile")

        description = d.pop("description", UNSET)

        domain = d.pop("domain", UNSET)

        def _parse_enet_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        enet_name = _parse_enet_name(d.pop("enet_name", UNSET))

        def _parse_features(
            data: object,
        ) -> Union["ZpodCreateFeaturesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_0 = ZpodCreateFeaturesType0.from_dict(data)

                return features_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ZpodCreateFeaturesType0", None, Unset], data)

        features = _parse_features(d.pop("features", UNSET))

        zpod_create = cls(
            endpoint_id=endpoint_id,
            name=name,
            profile=profile,
            description=description,
            domain=domain,
            enet_name=enet_name,
            features=features,
        )

        return zpod_create
