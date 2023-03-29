from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from zpodapi.lib.auth import get_current_user, update_last_connection_date  # noqa: F401
from zpodapi.lib.database import get_session  # noqa: F401
from zpodcommon import models as M

GetCurrentUserDepends = Depends(get_current_user)
GetCurrentUser = Annotated[M.User, GetCurrentUserDepends]

UpdateLastConnectionDateDepends = Depends(update_last_connection_date)
UpdateLastConnectionDate = Annotated[M.User, UpdateLastConnectionDateDepends]

GetSessionDepends = Depends(get_session)
GetSession = Annotated[Session, Depends(get_session)]
