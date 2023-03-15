from typing import Any

from sqlmodel import Session, SQLModel, or_, select


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self,
        *,
        _model: SQLModel | None = None,
        _use_or: bool = False,
        **kwargs: dict[Any, Any],
    ):
        model = _model or self.base_model
        sel = select(model)
        model_keys = set(model.__fields__.keys())
        criteria = []
        for attr, value in kwargs.items():
            if attr not in model_keys:
                raise AttributeError(f"Invalid attribute name: {attr}")
            if value:
                criteria.append(getattr(model, attr) == value)

        if criteria:
            sel = sel.where(or_(*criteria)) if _use_or else sel.where(*criteria)
        return self.session.exec(sel).all()

    def get(
        self,
        *,
        _model: SQLModel | None = None,
        **kwargs: dict[Any, Any],
    ):
        if not kwargs:
            raise AttributeError("Must have at least 1 attribute")

        model = _model or self.base_model
        model_keys = set(model.__fields__.keys())
        and_criteria = []
        for attr, value in kwargs.items():
            if attr not in model_keys:
                raise AttributeError(f"Invalid attribute name: {attr}")
            field_info = model.__fields__[attr].field_info
            if not field_info.primary_key and not field_info.unique:
                raise AttributeError(
                    f"Invalid attribute: {attr}.  "
                    "Must be either a primary_key or a unique field."
                )
            and_criteria.append(getattr(model, attr) == value)

        return self.session.exec(select(model).where(*and_criteria)).first()

    def create(
        self,
        *,
        item_in: SQLModel,
        _model: SQLModel | None = None,
    ):
        return self._create(
            item_in=item_in,
            _model=_model,
        )

    def _create(
        self,
        *,
        item_in: SQLModel,
        extra: dict | None = None,
        _model: SQLModel | None = None,
    ):  # sourcery skip: class-extract-method
        model = _model or self.base_model
        extra = extra or {}
        item = model(**item_in.dict(), **extra)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(
        self,
        *,
        item: SQLModel,
        item_in: SQLModel,
    ):
        data = item_in.dict(exclude_unset=True)
        data.pop("id", None)
        for key, value in data.items():
            setattr(item, key, value)

        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, *, item: SQLModel):
        self.session.delete(item)
        self.session.commit()
        return None
