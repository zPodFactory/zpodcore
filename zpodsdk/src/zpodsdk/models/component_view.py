from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ComponentView")


@_attrs_define
class ComponentView:
    """
    Attributes:
        component_description (str):
        component_name (str):
        component_uid (str):
        component_version (str):
        id (int):
    """

    component_description: str
    component_name: str
    component_uid: str
    component_version: str
    id: int

    def to_dict(self) -> dict[str, Any]:
        component_description = self.component_description

        component_name = self.component_name

        component_uid = self.component_uid

        component_version = self.component_version

        id = self.id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "component_description": component_description,
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        component_description = d.pop("component_description")

        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        id = d.pop("id")

        component_view = cls(
            component_description=component_description,
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            id=id,
        )

        return component_view
