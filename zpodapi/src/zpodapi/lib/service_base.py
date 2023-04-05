from sqlmodel import Session, SQLModel, or_

from zpodapi.lib.crud import Crud
from zpodcommon import models as M


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session, current_user: M.User):
        self.session: Session = session
        self.current_user: M.User = current_user
        self.crud = Crud(session=session, base_model=self.base_model)

    def get_all(self):
        return self.crud.select().all()

    def get_all_filtered(self, *, extra_criteria=None, use_or=False, **filters: dict):
        criteria = extra_criteria or []

        arg_criteria = self.crud.build_criteria_when_available(**filters)

        if use_or:
            criteria.append(or_(*arg_criteria))
        else:
            criteria.extend(arg_criteria)

        return self.crud.select(criteria=criteria).all()

    def get(self, *, value, column="id", extra_criteria=None):
        model_keys = set(self.base_model.__fields__.keys())
        if column not in model_keys:
            raise AttributeError(f"Invalid attribute name: {column}")

        criteria = (extra_criteria or []) + [getattr(self.base_model, column) == value]
        return self.crud.select(criteria=criteria).one_or_none()

    def create(self, *, item_in: SQLModel):
        return self.crud.create(item_in=item_in)

    def update(self, *, item: SQLModel, item_in: SQLModel):
        return self.crud.update(item=item, item_in=item_in)

    def delete(self, *, item: SQLModel):
        return self.crud.delete(item=item)
