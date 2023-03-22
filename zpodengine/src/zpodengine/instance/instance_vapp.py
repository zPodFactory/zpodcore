from prefect import task


@task(task_run_name="{instance_name}: create vapp")
def instance_vapp(
    instance_name: str,
):
    print("Create Instance VAPP")
