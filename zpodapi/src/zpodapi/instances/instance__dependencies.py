from fastapi import Depends, HTTPException, Path
from sqlmodel import Session

from zpodapi.lib import dependencies

from .instance__services import InstanceService
from .instance__types import InstanceIdType


def get_instance_record(
    *,
    session: Session = Depends(dependencies.get_session),
    id: InstanceIdType = Path(
        examples={
            "id": {"value": "1"},
            "id alternative": {"value": "id=1"},
            "name": {"value": "name=tanzu-lab"},
        },
    ),
):
    if instance := InstanceService(session=session).get(value=id):
        return instance
    raise HTTPException(status_code=404, detail="Instance not found")
