from rich import print
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import SQLModel

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M

from .endpoint__schemas import EndpointUpdate
from .endpoint__types import EndpointIdType
from .endpoint__utils import update_dictionary, zpod_endpoint_check


class EndpointService(ServiceBase):
    base_model: SQLModel = M.Endpoint

    def get(self, *, value, column="id"):
        column, value = EndpointIdType.parse(value)
        return super().get(value=value, column=column)

    def update(self, *, item: M.Endpoint, item_in: EndpointUpdate):
        for key, value in item_in.dict(exclude_unset=True).items():
            # specific code to handle nested dictionaries & JSON fields
            if key == "endpoints":
                update_dictionary(item.endpoints, value)
                value = item.endpoints

            setattr(item, key, value)

        # https://stackoverflow.com/questions/42559434/updates-to-json-field-dont-persist-to-db
        flag_modified(item, "endpoints")
        self.crud.save(item)
        return item

    def verify(self, *, item: M.Endpoint):
        # Verify endpoint status
        print(f"Verifying Endpoint {item.name}")
        return zpod_endpoint_check(item)
