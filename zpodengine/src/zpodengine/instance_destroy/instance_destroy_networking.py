from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.nsx import NsxClient
from zpodengine.lib import database


@task(task_run_name="{instance_name}: remove top level networking")
def instance_destroy_networking(
    instance_id: int,
    instance_name: str,
):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, instance_id)
        t1_name = f"T1-zPod-{instance.name}"
        t1_path = f"/infra/tier-1s/{t1_name}"
        print(f"Destroy {t1_name}")

        with NsxClient.auth_by_instance(instance) as nsx:
            # Destroy Connected Items (Segments)
            for connected in nsx.search(connectivity_path=fmt(t1_path)):
                # Destroy Connected Item Children (Segment BindingMaps)
                for connected_child in nsx.search(parent_path=fmt(connected["path"])):
                    delete(nsx, connected_child["path"])
                delete(nsx, connected["path"])

            # Destroy Children (LocaleServices)
            for child in nsx.search(parent_path=fmt(t1_path)):
                if child["resource_type"] not in ("SecurityFeatures", "PolicyNat"):
                    delete(nsx, child["path"])

            # Destroy T1
            delete(nsx, t1_path)


def delete(nsx, path):
    print(f"DELETE: {path}")
    nsx.delete(url=f"/v1{path}")


def fmt(txt):
    return txt.replace("/", "\\/")


if __name__ == "__main__":
    instance_destroy_networking.fn(22, "test")
