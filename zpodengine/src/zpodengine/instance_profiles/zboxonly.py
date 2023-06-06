from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)


def instance_profile_flow(
    instance_id: int,
    instance_name: str,
    wait_for=None,
):
    return instance_component_add(
        instance_id=instance_id,
        instance_name=instance_name,
        component_uid="zbox-11.7",
        wait_for=wait_for,
    )
