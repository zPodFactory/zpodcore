from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

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
        data (InstanceComponentViewData):  Example: {}.
    """

    component: "ComponentView"
    data: "InstanceComponentViewData"

    def to_dict(self) -> Dict[str, Any]:
        component = self.component.to_dict()

        data = self.data.to_dict()

        field_dict: Dict[str, Any] = {}
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

        return instance_component_view
