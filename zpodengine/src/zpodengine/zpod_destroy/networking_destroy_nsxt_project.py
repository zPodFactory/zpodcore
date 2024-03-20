from zpodcommon import models as M
from zpodengine import settings
from zpodengine.nsx_project_destroy.nsx_project_destroy import NsxProjectDestroy


def networking_destroy_nsxt_project(zpod: M.Zpod):
    # Destroy Project
    with NsxProjectDestroy(
        project_id=f"{settings.SITE_ID}-{zpod.name}-project",
        endpoint=zpod.endpoint,
    ) as npd:
        npd.destroy()
