import time

from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodcommon.lib.zboxapi import HTTPStatusError, RequestError


def execute_extra_post_scripts(
    zpod_component: M.ZpodComponent,
    zpod: M.Zpod,
    component: M.Component,
    zpodfactory_host: str,
    session: Session,
) -> None:
    """
    Execute additional post-installation scripts for NSX.
    Waits for the NSX cluster to be in a STABLE state.

    Args:
        zpod_component: The zPod component being installed
        zpod: The parent zPod
        component: The component being installed
        zpodfactory_host: The zPodFactory host
        session: The database session
    """
    print("Checking NSX cluster status")

    retries = 60
    wait_time = 60
    nsx_is_ready = False

    for retry in range(retries):
        try:
            nsx = NsxClient.auth_by_zpod(zpod=zpod_component.zpod)
            response = nsx.get(url="/api/v1/cluster/status")
            nsx_status = (
                response.safejson()
                .get("detailed_cluster_status")
                .get("overall_status")
            )
            print(f"NSX cluster status: {nsx_status}")

            if nsx_status != "STABLE":
                raise ValueError(f"NSX cluster status is {nsx_status}")

            nsx_is_ready = True
            break

        except (RequestError, HTTPStatusError) as e:
            print(
                f"Waiting for {e.request.url} {e} - Attempt {retry}/{retries}"
            )
            print("Waiting...")
            time.sleep(wait_time)

        except ValueError as e:
            print(f"{e} - Attempt {retry}/{retries}")
            print("Waiting...")
            time.sleep(wait_time)

    if not nsx_is_ready:
        raise ValueError(f"NSX cluster is not ready after {retries} attempts")

    print("NSX cluster is ready")

