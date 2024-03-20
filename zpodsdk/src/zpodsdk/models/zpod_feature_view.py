from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.zpod_feature_view_data import ZpodFeatureViewData


T = TypeVar("T", bound="ZpodFeatureView")


@_attrs_define
class ZpodFeatureView:
    """
    Attributes:
        data (ZpodFeatureViewData):
        id (int):
    """

    data: "ZpodFeatureViewData"
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
        from ..models.zpod_feature_view_data import ZpodFeatureViewData

        d = src_dict.copy()
        data = ZpodFeatureViewData.from_dict(d.pop("data"))

        id = d.pop("id")

        zpod_feature_view = cls(
            data=data,
            id=id,
        )

        return zpod_feature_view
