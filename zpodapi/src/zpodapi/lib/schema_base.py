from functools import partial
from typing import AbstractSet, Any, Dict, Mapping, Optional, Sequence, Union

from pydantic import ConfigDict
from sqlmodel import Field as SQLModelField
from sqlmodel import SQLModel
from sqlmodel.main import NoArgAnyCallable, Type, Undefined, UndefinedType

FIELD_ARGS = {
    "default": Undefined,
    "default_factory": None,
    "alias": None,
    "title": None,
    "description": None,
    "exclude": None,
    "include": None,
    "const": None,
    "gt": None,
    "ge": None,
    "lt": None,
    "le": None,
    "multiple_of": None,
    "min_items": None,
    "max_items": None,
    "min_length": None,
    "max_length": None,
    "allow_mutation": True,
    "regex": None,
    "primary_key": False,
    "foreign_key": None,
    "unique": False,
    "nullable": Undefined,
    "index": Undefined,
    "sa_column": Undefined,  # type: ignore
    "sa_column_args": Undefined,
    "sa_column_kwargs": Undefined,
    "schema_extra": None,
    "example": None,
}


def Field(
    default: Any = Undefined,
    default_args: dict[str, Any] | None = None,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Union[
        AbstractSet[Union[int, str]],
        Mapping[Union[int, str], Any],
        Any,
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
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    discriminator: Optional[str] = None,
    repr: bool = True,
    primary_key: Union[bool, UndefinedType] = Undefined,
    foreign_key: Any = Undefined,
    unique: Union[bool, UndefinedType] = Undefined,
    nullable: Union[bool, UndefinedType] = Undefined,
    index: Union[bool, UndefinedType] = Undefined,
    sa_type: Union[Type[Any], UndefinedType] = Undefined,
    sa_column_args: Union[Sequence[Any], UndefinedType] = Undefined,
    sa_column_kwargs: Union[Mapping[str, Any], UndefinedType] = Undefined,
    schema_extra: Optional[Dict[str, Any]] = None,
    example: Optional[str] = None,
) -> Any:
    schema_extra = schema_extra or {}
    ind_args = {k: v for k, v in locals().items() if v is not FIELD_ARGS.get(k)}
    ind_args.pop("default_args", None)

    default_args = default_args or {}
    for k in ("default", "default_args"):
        if k in default_args:
            raise KeyError(f"Invalid key in default_args: {k}")

    all_args = FIELD_ARGS | default_args | ind_args
    if all_args.get("example"):
        all_args["schema_extra"]["examples"] = [all_args["example"]]
    del all_args["example"]

    return SQLModelField(**all_args)


class SchemaBase(SQLModel):
    model_config = ConfigDict(extra="forbid")


Req = partial(Field, default=...)
Opt = partial(Field, default=None)
Empty = partial(Field, default="")
