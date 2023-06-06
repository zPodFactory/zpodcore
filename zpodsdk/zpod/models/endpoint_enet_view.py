from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="EndpointENetView")


@attr.s(auto_attribs=True)
class EndpointENetView:
    """
    Attributes:
        name (str):  Example: demo.
        project_id (str):  Example: zpod-demo-enet-project.
    """

    name: str
    project_id: str

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        project_id = self.project_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "project_id": project_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        project_id = d.pop("project_id")

        endpoint_enet_view = cls(
            name=name,
            project_id=project_id,
        )

        return endpoint_enet_view
