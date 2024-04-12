from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.endpoints_create import EndpointsCreate


T = TypeVar("T", bound="EndpointCreate")


@_attrs_define
class EndpointCreate:
    """
    Attributes:
        description (str):
        endpoints (EndpointsCreate):
        name (str):
    """

    description: str
    endpoints: "EndpointsCreate"
    name: str

    def to_dict(self) -> Dict[str, Any]:
        description = self.description

        endpoints = self.endpoints.to_dict()

        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "endpoints": endpoints,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.endpoints_create import EndpointsCreate

        d = src_dict.copy()
        description = d.pop("description")

        endpoints = EndpointsCreate.from_dict(d.pop("endpoints"))

        name = d.pop("name")

        endpoint_create = cls(
            description=description,
            endpoints=endpoints,
            name=name,
        )

        return endpoint_create
