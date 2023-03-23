from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.component_view import ComponentView
    from ..models.instance_component_view_data import InstanceComponentViewData


T = TypeVar("T", bound="InstanceComponentView")


@attr.s(auto_attribs=True)
class InstanceComponentView:
    """
    Attributes:
        component (ComponentView):
        data (InstanceComponentViewData):
    """

    component: "ComponentView"
    data: "InstanceComponentViewData"
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        component = self.component.to_dict()

        data = self.data.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "component": component,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.component_view import ComponentView
        from ..models.instance_component_view_data import InstanceComponentViewData

        d = src_dict.copy()
        component = ComponentView.from_dict(d.pop("component"))

        data = InstanceComponentViewData.from_dict(d.pop("data"))

        instance_component_view = cls(
            component=component,
            data=data,
        )

        instance_component_view.additional_properties = d
        return instance_component_view

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
