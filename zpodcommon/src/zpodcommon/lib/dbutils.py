from sqlalchemy import exc
from sqlmodel import select

from zpodcommon import models as M
from zpodcommon.lib import database


class DBUtils:
    #
    # DB helper class to query things easily.
    #

    @classmethod
    def get_setting_value(cls, name: str):
        with database.get_session_ctx() as session:
            try:
                setting = session.exec(
                    select(M.Setting).where(M.Setting.name == name)
                ).one()
                return setting.value
            except exc.NoResultFound:
                return None
