from sqlmodel import Session, SQLModel, or_

from zpodapi.lib.crud import Crud


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session):
        self.session = session
        self.crud = Crud(session=session, base_model=self.base_model)

    def get_all(self):
        return self.crud.select().all()

    def get_all_filtered(self, *, base_criteria=None, use_or=False, **filters: dict):
        criteria = base_criteria or []

        arg_criteria = self.crud.build_criteria_when_available(**filters)

        if use_or:
            criteria.append(or_(*arg_criteria))
        else:
            criteria.extend(arg_criteria)

        return self.crud.select(criteria=criteria).all()

    def get(self, *, value, column="id"):
        model_keys = set(self.base_model.__fields__.keys())

        if column not in model_keys:
            raise AttributeError(f"Invalid attribute name: {column}")
        field_info = self.base_model.__fields__[column].field_info
        if not field_info.primary_key and not field_info.unique:
            raise AttributeError(
                f"Invalid attribute: {column}.  "
                "Must be either a primary_key or a unique field."
            )
        return self.crud.select(
            criteria=[getattr(self.base_model, column) == value]
        ).first()

    def create(self, *, item_in: SQLModel):
        return self.crud.create(item_in=item_in)

    def update(self, *, item: SQLModel, item_in: SQLModel):
        return self.crud.update(item=item, item_in=item_in)

    def delete(self, *, item: SQLModel):
        return self.crud.delete(item=item)
