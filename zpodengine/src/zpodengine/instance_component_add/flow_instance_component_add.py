from prefect import flow

from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)


@flow(
    name="instance_component_add",
    flow_run_name="For {instance_name} add {component_uid}",
    log_prints=True,
)
def flow_instance_component_add(
    instance_id: int,
    instance_name: str,
    component_uid: str,
    data=None,
):
    instance_component_add(
        instance_id=instance_id,
        component_uid=component_uid,
        data=data,
    )


if __name__ == "__main__":
    print(flow_instance_component_add(1, "cds-10.2"))
