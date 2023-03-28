from fastapi import Depends, HTTPException, Path
from sqlmodel import Session

from zpodapi.lib import dependencies

from .user__services import UserService
from .user__types import UserIdType


def get_user_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: UserIdType = Path(
        examples={
            "id": {"value": "1"},
            "id alternative": {"value": "id=1"},
            "username": {"value": "username=jdoe"},
            "email": {"value": "email=jdoe@example.com"},
        },
    ),
):
    if user := UserService(session=session).get(value=id):
        return user
    raise HTTPException(status_code=404, detail="User not found")
