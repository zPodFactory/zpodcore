from prefect import task

# from zpodcommon import models as M
# from zpodengine.lib import database


@task(task_run_name="{label}: finalize")
def instance_component_add_finalize(
    keys: dict[str, str | int | None],
    label: str,
):
    print("Finalizing")
    # with database.get_session_ctx() as session:
    #     instance_component = session.get(M.InstanceComponent, keys)
