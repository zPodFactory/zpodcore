from prefect import flow

from zpodengine.lib.options import task_options_setup
from zpodengine.nsx_project_destroy.nsx_project_destroy import nsx_project_destroy


@flow(
    name="nsx_project_destroy",
    log_prints=True,
)
def flow_nsx_project_destroy(project_id: str, endpoint_id: int):
    options = task_options_setup(prefix=project_id)

    nsx_project_destroy.with_options(
        **options(name="nsx_project_destroy"),
    ).submit(
        project_id=project_id,
        endpoint_id=endpoint_id,
    )


if __name__ == "__main__":
    flow_nsx_project_destroy(project_id="zpod-demo-enet-project", endpoint_id=1)
