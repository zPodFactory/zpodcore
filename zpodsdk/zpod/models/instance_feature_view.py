from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.instance_feature_view_data import InstanceFeatureViewData


T = TypeVar("T", bound="InstanceFeatureView")


@_attrs_define
class InstanceFeatureView:
    """
    Attributes:
        data (InstanceFeatureViewData):
        id (int):
    """

    data: "InstanceFeatureViewData"
    id: int

    def to_dict(self) -> Dict[str, Any]:
        data = self.data.to_dict()

        id = self.id

        field_dict: Dict[str, Any] = {}
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

        return instance_feature_view
