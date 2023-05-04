import time
from datetime import datetime

from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodengine.lib import database

SEGMENT_MAX_WAIT_FOR_EMPTY = 120
SEGMENT_WAIT_BETWEEN_TRIES = 5


@task
def instance_destroy_networking(instance_id: int):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        t1_name = f"T1-zPod-{instance.name}"
        t1_path = f"/infra/tier-1s/{t1_name}"
        print(f"Destroy {t1_name}")

        with NsxClient.auth_by_instance(instance) as nsx:
            # Destroy Connected Items (Segments)
            for connected in nsx.search(connectivity_path=fmt(t1_path)):
                if connected["resource_type"] == "Segment":
                    segment_wait_for_empty(nsx, connected)

                    # Destroy Connected Item Children (Segment BindingMaps)
                    for connected_child in nsx.search(
                        parent_path=fmt(connected["path"])
                    ):
                        delete(nsx, connected_child["path"])
                delete(nsx, connected["path"])

            # Destroy Children (LocaleServices)
            for child in nsx.search(parent_path=fmt(t1_path)):
                if child["resource_type"] not in ("SecurityFeatures", "PolicyNat"):
                    delete(nsx, child["path"])

            # Destroy T1
            delete(nsx, t1_path)


def segment_wait_for_empty(nsx, segment):
    """Waits for the segment to have no ports/interfaces"""

    start = datetime.now()
    while (datetime.now() - start).seconds < SEGMENT_MAX_WAIT_FOR_EMPTY:
        ports = nsx.get(f"/v1{segment['path']}/ports").safejson()
        if ports["result_count"] == 0:
            print(
                f"Segment ({segment['display_name']}) has no ports / "
                "interfaces attached. Continuing."
            )
            break
        print(
            f"Segment ({segment['display_name']}) has ports / "
            "interfaces attached. Waiting..."
        )
        time.sleep(SEGMENT_WAIT_BETWEEN_TRIES)
    else:
        raise ValueError("Failed: Segment has connected ports / interfaces.")


def delete(nsx, path):
    print(f"DELETE: {path}")
    nsx.delete(url=f"/v1{path}")


def fmt(txt):
    return txt.replace("/", "\\/")


if __name__ == "__main__":
    instance_destroy_networking.fn(22, "test")
