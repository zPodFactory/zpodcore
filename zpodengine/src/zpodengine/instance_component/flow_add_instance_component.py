from prefect import flow

from zpodengine.instance_component.instance_component import add_instance_component


@flow(log_prints=True)
def flow_add_instance_component(
    instance_id: int,
    component_uid: str,
    extra_id: str = "",
    data=None,
):
    add_instance_component(
        instance_id=instance_id,
        component_uid=component_uid,
        extra_id=extra_id,
        data=data,
    )


if __name__ == "__main__":
    print(flow_add_instance_component(1, "cds-10.2"))
