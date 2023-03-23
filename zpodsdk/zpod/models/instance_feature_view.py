from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.instance_feature_view_data import InstanceFeatureViewData


T = TypeVar("T", bound="InstanceFeatureView")


@attr.s(auto_attribs=True)
class InstanceFeatureView:
    """
    Attributes:
        data (InstanceFeatureViewData):  Example: {'feature':'one'}.
        id (int):  Example: 1.
    """

    data: "InstanceFeatureViewData"
    id: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = self.data.to_dict()

        id = self.id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.instance_feature_view_data import InstanceFeatureViewData

        d = src_dict.copy()
        data = InstanceFeatureViewData.from_dict(d.pop("data"))

        id = d.pop("id")

        instance_feature_view = cls(
            data=data,
            id=id,
        )

        instance_feature_view.additional_properties = d
        return instance_feature_view

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
