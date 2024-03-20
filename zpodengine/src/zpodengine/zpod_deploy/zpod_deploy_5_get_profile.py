from prefect import task
from sqlmodel import select

from zpodcommon import models as M
from zpodengine.lib import database


@task
def zpod_deploy_get_profile(profile_name: str):
    with database.get_session_ctx() as session:
        profile = session.exec(
            select(M.Profile).where(
                M.Profile.name == profile_name.lower(),
            )
        ).one()
        print(profile.profile)
        return profile.profile
