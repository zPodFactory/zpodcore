from prefect import task

from zpodcommon import models as M
from zpodengine import settings
from zpodengine.lib import database
from zpodengine.nsx_project_destroy.nsx_project_destroy import NsxProjectDestroy

SEGMENT_MAX_WAIT_FOR_EMPTY = 120
SEGMENT_WAIT_BETWEEN_TRIES = 5


@task(tags=["atomic_operation"])
def instance_destroy_networking(instance_id: int):
    print("Destroy top level networking")

    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)

        # Destroy Project
        # This operation does not support concurrent calls.
        # Adding tags["atomic_operation"] to task will disable concurrency
        with NsxProjectDestroy(
            project_id=f"{settings.SITE_ID}-{instance.name}-project",
            endpoint=instance.endpoint,
        ) as npd:
            npd()


if __name__ == "__main__":
    instance_destroy_networking.fn(5)
