from pydantic import constr

from zpodapi.lib.schema_base import Field, SchemaBase


class D:
    name = {"example": "demo", "regex": r"^[A-Za-z0-9_-]+$"}
    project_id = {"example": "zpod-demo-enet-project"}


class EndpointENetCreate(SchemaBase):
    # NOTE: constr(to_lower) doesn't work with regex defined.  lower() is currently
    # handled in route.
    name: constr(to_lower=True) = Field(..., D.name)


class EndpointENetView(SchemaBase):
    project_id: str = Field(..., D.project_id)
    name: str = Field(..., D.name)
