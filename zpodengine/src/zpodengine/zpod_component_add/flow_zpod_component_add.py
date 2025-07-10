from prefect import flow

from zpodengine.zpod_component_add.zpod_component_add import (
    zpod_component_add,
)


@flow(
    name="zpod_component_add",
    log_prints=True,
)
def flow_zpod_component_add(
    zpod_id: int,
    zpod_name: str,
    component_uid: str,
    host_id: int | None = None,
    hostname: str | None = None,
    vcpu: int | None = None,
    vmem: int | None = None,
    vdisks: list[int] | None = None,
):
    zpod_component_add(
        zpod_id=zpod_id,
        zpod_name=zpod_name,
        component_uid=component_uid,
        host_id=host_id,
        hostname=hostname,
        vcpu=vcpu,
        vmem=vmem,
        vdisks=vdisks,
    )


if __name__ == "__main__":
    print(
        flow_zpod_component_add(
            zpod_id=1,
            zpod_name="Demo",
            component_uid="cds-10.2",
        )
    )
