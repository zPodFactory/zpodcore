from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import InstanceStatus
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
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup


def flow_failed(flow, flow_run, state):
    with database.get_session_ctx() as session:
        instance = session.get(M.Instance, flow_run.parameters["instance_id"])
        instance.status = InstanceStatus.DESTROY_FAILED
        session.add(instance)
        session.commit()


@flow(
    name="instance_destroy",
    flow_run_name="Destroy {instance_name}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_instance_destroy(
    instance_id: int,
    instance_name: str,
):
    options = task_options_setup(prefix=instance_name)

    prep = instance_destroy_prep.with_options(
        **options(name="prep"),
    ).submit(
        instance_id=instance_id,
    )

    dnsmasq = instance_destroy_dnsmasq.with_options(
        **options(name="dnsmasq"),
    ).submit(
        instance_id=instance_id,
        wait_for=[prep],
    )

    vapp = instance_destroy_vapp.with_options(
        **options(name="vapp"),
    ).submit(
        instance_id=instance_id,
        wait_for=[prep],
    )

    networking = instance_destroy_networking.with_options(
        **options(name="top level networking"),
    ).submit(
        instance_id=instance_id,
        wait_for=[vapp],
    )

    instance_destroy_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        instance_id=instance_id,
        wait_for=[dnsmasq, vapp, networking],
    )


if __name__ == "__main__":
    flow_instance_destroy(
        instance_id=3,
        instance_name="abc",
    )
