from prefect import flow

from zpodengine.instance_destroy.instance_destroy_dnsmasq import (
    instance_destroy_dnsmasq,
)
from zpodengine.instance_destroy.instance_destroy_finalize import (
    instance_destroy_finalize,
)
from zpodengine.instance_destroy.instance_destroy_networking import (
    instance_destroy_networking,
)
from zpodengine.instance_destroy.instance_destroy_prep import instance_destroy_prep
from zpodengine.instance_destroy.instance_destroy_vapp import instance_destroy_vapp


@flow(
    name="instance_destroy",
    flow_run_name="destroy_{instance_name}",
    log_prints=True,
)
def flow_instance_destroy(
    instance_id: int,
    instance_name: str,
):
    prep = instance_destroy_prep.submit(
        instance_id=instance_id,
        instance_name=instance_name,
    )

    dnsmasq = instance_destroy_dnsmasq.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[prep],
    )

    vapp = instance_destroy_vapp.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[prep],
    )

    networking = instance_destroy_networking.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[vapp],
    )

    instance_destroy_finalize.submit(
        instance_id=instance_id,
        instance_name=instance_name,
        wait_for=[dnsmasq, vapp, networking],
    )


if __name__ == "__main__":
    flow_instance_destroy(instance_id=3, instance_name="abc")
