import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.instance_status import InstanceStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoint_view import EndpointView
    from ..models.instance_component_view import InstanceComponentView
    from ..models.instance_feature_view import InstanceFeatureView
    from ..models.instance_network_view import InstanceNetworkView
    from ..models.instance_permission_view import InstancePermissionView


T = TypeVar("T", bound="InstanceView")


@_attrs_define
class InstanceView:
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
        status (InstanceStatus):
        components (Union[Unset, List['InstanceComponentView']]):
        features (Union[Unset, List['InstanceFeatureView']]):
        networks (Union[Unset, List['InstanceNetworkView']]):
        permissions (Union[Unset, List['InstancePermissionView']]):
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
    status: InstanceStatus
    components: Union[Unset, List["InstanceComponentView"]] = UNSET
    features: Union[Unset, List["InstanceFeatureView"]] = UNSET
    networks: Union[Unset, List["InstanceNetworkView"]] = UNSET
    permissions: Union[Unset, List["InstancePermissionView"]] = UNSET

    def to_dict(self) -> Dict[str, Any]:
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

        features: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.features, Unset):
            features = []
            for features_item_data in self.features:
                features_item = features_item_data.to_dict()
                features.append(features_item)

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
        from ..models.instance_component_view import InstanceComponentView
        from ..models.instance_feature_view import InstanceFeatureView
        from ..models.instance_network_view import InstanceNetworkView
        from ..models.instance_permission_view import InstancePermissionView

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

        status = InstanceStatus(d.pop("status"))

        components = []
        _components = d.pop("components", UNSET)
        for components_item_data in _components or []:
            components_item = InstanceComponentView.from_dict(components_item_data)

            components.append(components_item)

        features = []
        _features = d.pop("features", UNSET)
        for features_item_data in _features or []:
            features_item = InstanceFeatureView.from_dict(features_item_data)

            features.append(features_item)

        networks = []
        _networks = d.pop("networks", UNSET)
        for networks_item_data in _networks or []:
            networks_item = InstanceNetworkView.from_dict(networks_item_data)

            networks.append(networks_item)

        permissions = []
        _permissions = d.pop("permissions", UNSET)
        for permissions_item_data in _permissions or []:
            permissions_item = InstancePermissionView.from_dict(permissions_item_data)

            permissions.append(permissions_item)

        instance_view = cls(
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

        return instance_view
