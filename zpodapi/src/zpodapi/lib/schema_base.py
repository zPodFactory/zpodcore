from functools import partial
from typing import AbstractSet, Any, Dict, Mapping, Optional, Sequence, Union

from pydantic.fields import Undefined, UndefinedType
from pydantic.typing import NoArgAnyCallable
from sqlalchemy import Column
from sqlmodel import Field as SQLModelField
from sqlmodel import SQLModel

FIELD_ARGS = dict(
    default=Undefined,
    default_factory=None,
    alias=None,
    title=None,
    description=None,
    exclude=None,
    include=None,
    const=None,
    gt=None,
    ge=None,
    lt=None,
    le=None,
    multiple_of=None,
    min_items=None,
    max_items=None,
    min_length=None,
    max_length=None,
    allow_mutation=True,
    regex=None,
    primary_key=False,
    foreign_key=None,
    unique=False,
    nullable=Undefined,
    index=Undefined,
    sa_column=Undefined,  # type: ignore
    sa_column_args=Undefined,
    sa_column_kwargs=Undefined,
    schema_extra=None,
    example=None,
    hidden=False,
)


def Field(
    default: Any = Undefined,
    default_args: dict[str, Any] | None = None,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    primary_key: bool = False,
    foreign_key: Optional[Any] = None,
    unique: bool = False,
    nullable: Union[bool, UndefinedType] = Undefined,
    index: Union[bool, UndefinedType] = Undefined,
    sa_column: Union[Column, UndefinedType] = Undefined,  # type: ignore
    sa_column_args: Union[Sequence[Any], UndefinedType] = Undefined,
    sa_column_kwargs: Union[Mapping[str, Any], UndefinedType] = Undefined,
    schema_extra: Optional[Dict[str, Any]] = None,
    example: Optional[str] = None,
    hidden: bool = False,
) -> Any:
    schema_extra = schema_extra or {}
    ind_args = {k: v for k, v in locals().items() if v is not FIELD_ARGS.get(k)}
    ind_args.pop("default_args", None)

    default_args = default_args or {}
    for k in ("default", "default_args"):
        if k in default_args:
            raise KeyError(f"Invalid key in default_args: {k}")

    all_args = FIELD_ARGS | default_args | ind_args
    for k in ("example", "hidden"):
        if all_args.get(k):
            all_args["schema_extra"][k] = all_args[k]
    del all_args["example"], all_args["hidden"]

    return SQLModelField(**all_args)


class SchemaBase(SQLModel):
    class Config:
        extra = "forbid"

        @staticmethod
        def schema_extra(schema: dict, _):
            schema["properties"] = {
                k: v
                for k, v in schema.get("properties", {}).items()
                if not v.get("hidden", False)
            }


Req = partial(Field, default=...)
Opt = partial(Field, default=None)
Empty = partial(Field, default="")
