from prefect import task

from zpodcommon import models as M
from zpodengine.lib import database


@task(task_run_name="{label}: execute post_scripts")
def instance_component_add_post_scripts(
    keys: dict[str, str | int | None],
    label: str,
):
    with database.get_session_ctx() as session:
        instance_component = session.get(M.InstanceComponent, keys)
        custom_postscripts = instance_component.data.get("postscripts", [])
        print(f"Run Postscripts: {custom_postscripts}")
