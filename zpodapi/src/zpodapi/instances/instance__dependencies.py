from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from .instance__services import InstanceService


def get_instance_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: int,
):
    if instance := InstanceService(session=session).get(id=id):
        return instance
    raise HTTPException(status_code=404, detail="Instance not found")
