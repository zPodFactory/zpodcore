from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="ComponentViewFull")


@attr.s(auto_attribs=True)
class ComponentViewFull:
    """
    Attributes:
        component_description (str):  Example: VMware Cloud Director Availabilty.
        component_name (str):  Example: vcda.
        component_uid (str):  Example: vcda-4.4.1.
        component_version (str):  Example: 4.4.1.
        enabled (bool):
        filename (str):  Example: VMware-Cloud-Director-Availability-Provider-4.4.1.4448762-b80bae6591_OVF10.ova.
        id (str):  Example: 1.
        jsonfile (str):  Example: /library/default/vmware/vmware_cloud_director_availability/4.4.1.json.
        library_name (str):  Example: main.
        status (str):  Example: SCHEDULED.
    """

    component_description: str
    component_name: str
    component_uid: str
    component_version: str
    enabled: bool
    filename: str
    id: str
    jsonfile: str
    library_name: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        component_description = self.component_description
        component_name = self.component_name
        component_uid = self.component_uid
        component_version = self.component_version
        enabled = self.enabled
        filename = self.filename
        id = self.id
        jsonfile = self.jsonfile
        library_name = self.library_name
        status = self.status

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "component_description": component_description,
                "component_name": component_name,
                "component_uid": component_uid,
                "component_version": component_version,
                "enabled": enabled,
                "filename": filename,
                "id": id,
                "jsonfile": jsonfile,
                "library_name": library_name,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        component_description = d.pop("component_description")

        component_name = d.pop("component_name")

        component_uid = d.pop("component_uid")

        component_version = d.pop("component_version")

        enabled = d.pop("enabled")

        filename = d.pop("filename")

        id = d.pop("id")

        jsonfile = d.pop("jsonfile")

        library_name = d.pop("library_name")

        status = d.pop("status")

        component_view_full = cls(
            component_description=component_description,
            component_name=component_name,
            component_uid=component_uid,
            component_version=component_version,
            enabled=enabled,
            filename=filename,
            id=id,
            jsonfile=jsonfile,
            library_name=library_name,
            status=status,
        )

        return component_view_full
