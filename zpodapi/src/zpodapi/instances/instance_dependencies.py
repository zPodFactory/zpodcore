from fastapi import Depends, HTTPException
from sqlmodel import Session

from zpodapi.lib import dependencies

from . import instance_services


def get_instance_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: int,
):
    print(id)
    if instance := instance_services.get(
        session=session,
        id=id,
    ):
        return instance
    raise HTTPException(status_code=404, detail="Instance not found")
