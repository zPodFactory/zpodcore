from fastapi import HTTPException, status
from sqlmodel import Session, select

from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus


def walk_profile(profile_obj):
    for profile_item in profile_obj:
        if isinstance(profile_item, list):
            yield from profile_item
        else:
            yield profile_item


def validate_profile(session: Session, profile_obj: list):
    # Get all component_uids in profile
    component_uids = {x["component_uid"] for x in walk_profile(profile_obj)}

    # Get component_uid and status for db
    components = dict(
        session.exec(
            select(
                M.Component.component_uid,
                M.Component.status,
            ).where(
                M.Component.component_uid.in_(component_uids),
            )
        ).fetchall()
    )

    # Validate
    errors = []
    for component_uid in component_uids:
        # Validate that component_uid is in db
        if component_uid not in components:
            errors.append(f"Invalid component_uid: {component_uid}")
        # Validate that component is active
        elif components.get(component_uid) != ComponentStatus.ACTIVE:
            errors.append(f"Component is not ACTIVE: {component_uid}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="\n  ".join(errors),
        )
