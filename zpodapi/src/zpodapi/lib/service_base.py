from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from sqlmodel import Session, SQLModel

from zpodapi.lib.crud import Crud
from zpodcommon import models as M


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session, current_user: M.User):
        self.session: Session = session
        self.current_user: M.User = current_user
        self.crud = Crud(session=session, base_model=self.base_model)

    def convert_schema(self, schema, item_in):
        # If already proper schema, just return it
        if type(item_in) == schema:
            return item_in
        try:
            return schema(**item_in.dict(exclude_unset=True))
        except ValidationError as e:
            raise RequestValidationError(errors=[ErrorWrapper(e, ("body"))]) from e
