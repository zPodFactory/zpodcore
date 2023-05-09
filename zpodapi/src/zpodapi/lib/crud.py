from typing import Any

from sqlalchemy import func
from sqlmodel import Session, SQLModel, or_, select
from sqlmodel.engine.result import Result


class Crud:
    def __init__(
        self,
        session: Session,
        base_model: SQLModel,
    ):
        self.session = session
        self.base_model = base_model

    def build_truthy_criteria(
        self,
        *,
        model_: SQLModel = None,
        **filters: dict,
    ):
        model = model_ or self.base_model
        model_keys = set(self.base_model.__fields__.keys())

        ret = []
        for column, value in filters.items():
            column, insensitive, _ = column.partition("_insensitive")
            if column not in model_keys:
                raise AttributeError(f"Invalid attribute name: {column}")

            # Add each truthy item to the criteria
            if value:
                if insensitive:
                    ret.append(func.lower(getattr(model, column)) == value.lower())
                else:
                    ret.append(getattr(model, column) == value)
        return ret

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

    def get(
        self,
        *,
        where_extra: list | None = None,
        model: SQLModel | None = None,
        **filters: dict[str, Any],
    ):
        arg_criteria = self.build_truthy_criteria(**filters)
        if len(arg_criteria) == 0:
            raise AttributeError("Must have at least one filter")

        where = (where_extra or []) + arg_criteria
        return self.select(where=where, model=model).one_or_none()

    def get_all(
        self,
        model: SQLModel | None = None,
    ):
        return self.select(model=model).all()

    def get_all_filtered(
        self,
        *,
        where_extra: list = None,
        use_or: bool = False,
        model: SQLModel | None = None,
        **filters: dict[str, Any],
    ):
        where = where_extra or []

        arg_criteria = self.build_truthy_criteria(**filters)

        if use_or:
            where.append(or_(*arg_criteria))
        else:
            where.extend(arg_criteria)

        return self.select(where=where, model=model).all()

    def save(self, item: SQLModel):
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def select(
        self,
        *,
        where: list | None = None,
        model: SQLModel | None = None,
    ) -> Result[Any]:
        model = model or self.base_model
        sel = select(model)
        if where:
            sel = sel.where(*where)
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
