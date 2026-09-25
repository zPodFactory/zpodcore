from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="EndpointENetView")


@_attrs_define
class EndpointENetView:
    """
    Attributes:
        name (str):
        project_id (str):
    """

    name: str
    project_id: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        project_id = self.project_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "project_id": project_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        project_id = d.pop("project_id")

        endpoint_enet_view = cls(
            name=name,
            project_id=project_id,
        )

        return endpoint_enet_view
