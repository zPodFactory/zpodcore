from prefect import flow

from zpodengine.instance_component_add.instance_component_add import (
    instance_component_add,
)


@flow(
    name="instance_component_add",
    log_prints=True,
)
def flow_instance_component_add(
    instance_id: int,
    instance_name: str,
    component_uid: str,
    host_id: str | None = None,
    hostname: str | None = None,
    vcpu: int | None = None,
    vmem: int | None = None,
):
    instance_component_add(
        instance_id=instance_id,
        instance_name=instance_name,
        component_uid=component_uid,
        host_id=host_id,
        hostname=hostname,
        vcpu=vcpu,
        vmem=vmem,
    )


if __name__ == "__main__":
    print(
        flow_instance_component_add(
            instance_id=1,
            instance_name="Demo",
            component_uid="cds-10.2",
        )
    )
