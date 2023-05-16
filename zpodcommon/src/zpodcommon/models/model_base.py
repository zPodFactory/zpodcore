from typing import Any

from sqlmodel import Column, SQLModel
from sqlmodel.main import SQLModelMetaclass


class ColumnCloningMetaclass(SQLModelMetaclass):
    # Keep sa_column* columns in the proper order
    def __setattr__(cls, name: str, value: Any) -> None:
        if isinstance(value, Column):
            return super().__setattr__(name, value.copy())
        return super().__setattr__(name, value)


class ModelBase(SQLModel, metaclass=ColumnCloningMetaclass):
    pass
