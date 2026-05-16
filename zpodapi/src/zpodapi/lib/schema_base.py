"""Schema utilities for zpodapi route models.

`Field()` here wraps `sqlmodel.Field` so callers can pass an OpenAPI metadata
dict positionally — e.g. `Field(default, {"example": "x"})` — and the example
flows into `json_schema_extra` for the generated OpenAPI/FastAPI docs.

Compatibility shim history: previously this module replicated the full
pydantic-v1 `Field` argument list and imported sqlmodel's private internals.
None of those v1 args were used by any caller (verified) and the internal
imports were removed in sqlmodel 0.0.19+. The module is now a small,
forward-only helper on top of the public sqlmodel/pydantic v2 API.
"""

from typing import Any

from pydantic import ConfigDict
from sqlmodel import Field as SQLModelField
from sqlmodel import SQLModel


def Field(
    default: Any = ...,
    default_args: dict[str, Any] | None = None,
    *,
    example: Any = None,
    **kwargs: Any,
) -> Any:
    """`sqlmodel.Field` plus an optional metadata dict for OpenAPI examples.

    `default_args` (positional) is typically `{"example": "..."}`; its
    contents are merged into `schema_extra` so the example appears in the
    generated OpenAPI schema. `example=` may also be passed as a kwarg for
    the same effect.

    Note: sqlmodel 0.0.38 still exposes its parameter as `schema_extra`
    (a v1-era name), but it forwards the dict to pydantic v2's
    `json_schema_extra` internally — same end result in the OpenAPI doc.
    """
    schema_extra: dict[str, Any] = dict(kwargs.pop("schema_extra", {}) or {})

    da = dict(default_args or {})
    example_value = example if example is not None else da.pop("example", None)
    if example_value is not None:
        schema_extra["examples"] = [example_value]
    schema_extra.update(da)

    if schema_extra:
        kwargs["schema_extra"] = schema_extra
    return SQLModelField(default, **kwargs)


class SchemaBase(SQLModel):
    """Base class for request/response schemas — rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")
