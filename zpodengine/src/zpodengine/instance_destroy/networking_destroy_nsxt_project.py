from zpodcommon import models as M
from zpodengine import settings
from zpodengine.nsx_project_destroy.nsx_project_destroy import NsxProjectDestroy


def networking_destroy_nsxt_project(instance: M.Instance):
    # Destroy Project
    with NsxProjectDestroy(
        project_id=f"{settings.SITE_ID}-{instance.name}-project",
        endpoint=instance.endpoint,
    ) as npd:
        npd.destroy()
