from typing import Any

from sqlmodel import Session, SQLModel, select
from sqlmodel.engine.result import Result


class Crud:
    def __init__(
        self,
        session: Session,
        base_model: SQLModel,
    ):
        self.session = session
        self.base_model = base_model

    def build_criteria_when_available(
        self,
        *,
        model_: SQLModel = None,
        **filters: dict,
    ):
        model = model_ or self.base_model
        model_keys = set(self.base_model.__fields__.keys())

        for column in filters:
            if column not in model_keys:
                raise AttributeError(f"Invalid attribute name: {column}")

        # Add each truthy item to the criteria
        return [
            getattr(model, column) == value
            for column, value in filters.items()
            if value
        ]

    def create(
        self,
        *,
        item_in: SQLModel,
        extra: dict | None = None,
        model: SQLModel | None = None,
    ):
        model = model or self.base_model
        extra = extra or {}
        item = model(**item_in.dict(), **extra)
        return self.save(item=item)

    def delete(
        self,
        *,
        item: SQLModel,
    ):
        self.session.delete(item)
        self.session.commit()
        return None

    def save(self, item: SQLModel):
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def select(
        self,
        *,
        criteria: list | None = None,
        model: SQLModel | None = None,
    ) -> Result[Any]:
        model = model or self.base_model
        sel = select(model)
        if criteria:
            sel = sel.where(*criteria)
        return self.session.exec(sel)

    def update(
        self,
        *,
        item: SQLModel,
        item_in: SQLModel,
        remove_id=True,
    ):
        data = item_in.dict(exclude_unset=True)
        if remove_id:
            data.pop("id", None)
        for key, value in data.items():
            setattr(item, key, value)
        return self.save(item=item)


if __name__ == "__main__":
    from zpodapi.lib import database

    session = database.get_session_raw()
