from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

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
        components (list[ZpodComponentView] | Unset):
        features (None | Unset | ZpodViewFeaturesType0):
        networks (list[ZpodNetworkView] | Unset):
        permissions (list[ZpodPermissionView] | Unset):
    """

    creation_date: datetime.datetime
    description: str
    domain: str
    endpoint: EndpointView
    id: int
    last_modified_date: datetime.datetime
    name: str
    password: str
    profile: str
    status: ZpodStatus
    components: list[ZpodComponentView] | Unset = UNSET
    features: None | Unset | ZpodViewFeaturesType0 = UNSET
    networks: list[ZpodNetworkView] | Unset = UNSET
    permissions: list[ZpodPermissionView] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
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

        components: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.components, Unset):
            components = []
            for components_item_data in self.components:
                components_item = components_item_data.to_dict()
                components.append(components_item)

        features: dict[str, Any] | None | Unset
        if isinstance(self.features, Unset):
            features = UNSET
        elif isinstance(self.features, ZpodViewFeaturesType0):
            features = self.features.to_dict()
        else:
            features = self.features

        networks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.networks, Unset):
            networks = []
            for networks_item_data in self.networks:
                networks_item = networks_item_data.to_dict()
                networks.append(networks_item)

        permissions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = []
            for permissions_item_data in self.permissions:
                permissions_item = permissions_item_data.to_dict()
                permissions.append(permissions_item)

        field_dict: dict[str, Any] = {}

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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoint_view import EndpointView
        from ..models.zpod_component_view import ZpodComponentView
        from ..models.zpod_network_view import ZpodNetworkView
        from ..models.zpod_permission_view import ZpodPermissionView
        from ..models.zpod_view_features_type_0 import ZpodViewFeaturesType0

        d = dict(src_dict)
        creation_date = datetime.datetime.fromisoformat(d.pop("creation_date"))

        description = d.pop("description")

        domain = d.pop("domain")

        endpoint = EndpointView.from_dict(d.pop("endpoint"))

        id = d.pop("id")

        last_modified_date = datetime.datetime.fromisoformat(
            d.pop("last_modified_date")
        )

        name = d.pop("name")

        password = d.pop("password")

        profile = d.pop("profile")

        status = ZpodStatus(d.pop("status"))

        _components = d.pop("components", UNSET)
        components: list[ZpodComponentView] | Unset = UNSET
        if _components is not UNSET:
            components = []
            for components_item_data in _components:
                components_item = ZpodComponentView.from_dict(components_item_data)

                components.append(components_item)

        def _parse_features(data: object) -> None | Unset | ZpodViewFeaturesType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                features_type_0 = ZpodViewFeaturesType0.from_dict(data)

                return features_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | ZpodViewFeaturesType0, data)

        features = _parse_features(d.pop("features", UNSET))

        _networks = d.pop("networks", UNSET)
        networks: list[ZpodNetworkView] | Unset = UNSET
        if _networks is not UNSET:
            networks = []
            for networks_item_data in _networks:
                networks_item = ZpodNetworkView.from_dict(networks_item_data)

                networks.append(networks_item)

        _permissions = d.pop("permissions", UNSET)
        permissions: list[ZpodPermissionView] | Unset = UNSET
        if _permissions is not UNSET:
            permissions = []
            for permissions_item_data in _permissions:
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
