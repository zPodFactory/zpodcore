from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from zpodapi.lib.auth import get_current_user, get_current_user_and_update  # noqa: F401
from zpodapi.lib.database import get_session  # noqa: F401
from zpodcommon import models as M

GetCurrentUserDepends = Depends(get_current_user)
GetCurrentUser = Annotated[M.User, GetCurrentUserDepends]

GetCurrentUserAndUpdateDepends = Depends(get_current_user_and_update)
GetCurrentUserAndUpdate = Annotated[M.User, GetCurrentUserAndUpdateDepends]

GetSessionDepends = Depends(get_session)
GetSession = Annotated[Session, Depends(get_session)]
