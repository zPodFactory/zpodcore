from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlmodel import Session, SQLModel

from zpodapi.lib.crud import Crud
from zpodcommon import models as M


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session, current_user: M.User):
        self.session: Session = session
        self.crud = Crud(session=session, base_model=self.base_model)
        self.current_user: M.User = current_user
        self.is_superadmin = current_user.superadmin

    def convert_schema(self, schema, item_in):
        # If already proper schema, just return it
        if type(item_in) == schema:
            return item_in
        try:
            return schema(**item_in.model_dump(exclude_unset=True))
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e
