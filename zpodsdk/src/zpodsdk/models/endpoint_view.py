from typing import Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

from ..models.endpoint_status import EndpointStatus

T = TypeVar("T", bound="EndpointView")


@_attrs_define
class EndpointView:
    """
    Attributes:
        description (str):
        id (int):
        name (str):
        status (EndpointStatus):
    """

    description: str
    id: int
    name: str
    status: EndpointStatus

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        id = self.id

        name = self.name

        status = self.status.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "id": id,
                "name": name,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        description = d.pop("description")

        id = d.pop("id")

        name = d.pop("name")

        status = EndpointStatus(d.pop("status"))

        endpoint_view = cls(
            description=description,
            id=id,
            name=name,
            status=status,
        )

        return endpoint_view
