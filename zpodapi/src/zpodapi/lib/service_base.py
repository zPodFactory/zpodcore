from sqlmodel import Session, SQLModel

from zpodapi.lib.crud import Crud
from zpodcommon import models as M


class ServiceBase:
    base_model: SQLModel = None

    def __init__(self, session: Session, current_user: M.User):
        self.session: Session = session
        self.current_user: M.User = current_user
        self.crud = Crud(session=session, base_model=self.base_model)
