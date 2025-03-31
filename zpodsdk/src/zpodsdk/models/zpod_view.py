import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.zpod_status import ZpodStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoint_view import EndpointView
    from ..models.zpod_component_view import ZpodComponentView
    from ..models.zpod_network_view import ZpodNetworkView
    from ..models.zpod_permission_view import ZpodPermissionView
    from ..models.zpod_view_features_type_0 import ZpodViewFeaturesType0


T = TypeVar("T", bound="ZpodView")


@_attrs_define
class ZpodView:
    """
    Attributes:
        creation_date (datetime.datetime):
        description (str):
        domain (str):
        endpoint (EndpointView):
        id (int):
        last_modified_date (datetime.datetime):
        name (str):
        password (str):
        profile (str):
        status (ZpodStatus):
        components (Union[Unset, List['ZpodComponentView']]):
        features (Union['ZpodViewFeaturesType0', None, Unset]):
        networks (Union[Unset, List['ZpodNetworkView']]):
        permissions (Union[Unset, List['ZpodPermissionView']]):
    """

    creation_date: datetime.datetime
    description: str
    domain: str
    endpoint: "EndpointView"
    id: int
    last_modified_date: datetime.datetime
    name: str
    password: str
    profile: str
    status: ZpodStatus
    components: Union[Unset, List["ZpodComponentView"]] = UNSET
    features: Union["ZpodViewFeaturesType0", None, Unset] = UNSET
    networks: Union[Unset, List["ZpodNetworkView"]] = UNSET
    permissions: Union[Unset, List["ZpodPermissionView"]] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        from ..models.zpod_view_features_type_0 import ZpodViewFeaturesType0

        creation_date = self.creation_date.isoformat()

        description = self.description

        domain = self.domain

        endpoint = self.endpoint.to_dict()

        id = self.id

        last_modified_date = self.last_modified_date.isoformat()

        name = self.name

        password = self.password

        profile = self.profile

        status = self.status.value

        components: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.components, Unset):
            components = []
            for components_item_data in self.components:
                components_item = components_item_data.to_dict()
                components.append(components_item)

        features: Union[Dict[str, Any], None, Unset]
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, ZpodViewFeaturesType0):
            features = self.features.to_dict()
        else:
            features = self.features

        networks: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.networks, Unset):
            networks = []
            for networks_item_data in self.networks:
                networks_item = networks_item_data.to_dict()
                networks.append(networks_item)

        permissions: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = []
            for permissions_item_data in self.permissions:
                permissions_item = permissions_item_data.to_dict()
                permissions.append(permissions_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "creation_date": creation_date,
                "description": description,
                "domain": domain,
                "endpoint": endpoint,
                "id": id,
                "last_modified_date": last_modified_date,
                "name": name,
                "password": password,
                "profile": profile,
                "status": status,
            }
        )
        if components is not UNSET:
            field_dict["components"] = components
        if features is not UNSET:
            field_dict["features"] = features
        if networks is not UNSET:
            field_dict["networks"] = networks
        if permissions is not UNSET:
            field_dict["permissions"] = permissions

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoint_view import EndpointView
        from ..models.zpod_component_view import ZpodComponentView
        from ..models.zpod_network_view import ZpodNetworkView
        from ..models.zpod_permission_view import ZpodPermissionView
        from ..models.zpod_view_features_type_0 import ZpodViewFeaturesType0

        d = src_dict.copy()
        creation_date = isoparse(d.pop("creation_date"))

        description = d.pop("description")

        domain = d.pop("domain")

        endpoint = EndpointView.from_dict(d.pop("endpoint"))

        id = d.pop("id")

        last_modified_date = isoparse(d.pop("last_modified_date"))

        name = d.pop("name")

        password = d.pop("password")

        profile = d.pop("profile")

        status = ZpodStatus(d.pop("status"))

        components = []
        _components = d.pop("components", UNSET)
        for components_item_data in _components or []:
            components_item = ZpodComponentView.from_dict(components_item_data)

            components.append(components_item)

        def _parse_features(
            data: object,
        ) -> Union["ZpodViewFeaturesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_0 = ZpodViewFeaturesType0.from_dict(data)

                return features_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ZpodViewFeaturesType0", None, Unset], data)

        features = _parse_features(d.pop("features", UNSET))

        networks = []
        _networks = d.pop("networks", UNSET)
        for networks_item_data in _networks or []:
            networks_item = ZpodNetworkView.from_dict(networks_item_data)

            networks.append(networks_item)

        permissions = []
        _permissions = d.pop("permissions", UNSET)
        for permissions_item_data in _permissions or []:
            permissions_item = ZpodPermissionView.from_dict(permissions_item_data)

            permissions.append(permissions_item)

        zpod_view = cls(
            creation_date=creation_date,
            description=description,
            domain=domain,
            endpoint=endpoint,
            id=id,
            last_modified_date=last_modified_date,
            name=name,
            password=password,
            profile=profile,
            status=status,
            components=components,
            features=features,
            networks=networks,
            permissions=permissions,
        )

        return zpod_view
