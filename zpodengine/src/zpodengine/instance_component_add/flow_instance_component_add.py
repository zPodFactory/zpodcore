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
    profile_item: dict,
):
    instance_component_add(
        instance_id=instance_id,
        profile_item=profile_item,
    )


if __name__ == "__main__":
    print(
        flow_instance_component_add(
            instance_id=1,
            profile_item=dict(component_uid="cds-10.2"),
        )
    )
