from prefect import flow

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database
from zpodengine.lib.options import task_options_setup
from zpodengine.zpod_destroy.zpod_destroy_1_prep import zpod_destroy_prep
from zpodengine.zpod_destroy.zpod_destroy_2_dnsmasq import (
    zpod_destroy_dnsmasq,
)
from zpodengine.zpod_destroy.zpod_destroy_3_vapp import zpod_destroy_vapp
from zpodengine.zpod_destroy.zpod_destroy_4_networking import (
    zpod_destroy_networking,
)
from zpodengine.zpod_destroy.zpod_destroy_5_finalize import (
    zpod_destroy_finalize,
)


def flow_failed(flow, flow_run, state):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, flow_run.parameters["zpod_id"])
        zpod.status = ZpodStatus.DESTROY_FAILED
        session.add(zpod)
        session.commit()


@flow(
    name="zpod_destroy",
    flow_run_name="Destroy {zpod_name}",
    on_failure=[flow_failed],
    log_prints=True,
)
def flow_zpod_destroy(
    zpod_id: int,
    zpod_name: str,
):
    options = task_options_setup(prefix=zpod_name)

    prep = zpod_destroy_prep.with_options(
        **options(name="prep"),
    ).submit(
        zpod_id=zpod_id,
    )

    dnsmasq = zpod_destroy_dnsmasq.with_options(
        **options(name="dnsmasq"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[prep],
    )

    vapp = zpod_destroy_vapp.with_options(
        **options(name="vapp"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[prep],
    )

    networking = zpod_destroy_networking.with_options(
        **options(name="top level networking"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[vapp],
    )

    zpod_destroy_finalize.with_options(
        **options(name="finalize"),
    ).submit(
        zpod_id=zpod_id,
        wait_for=[dnsmasq, vapp, networking],
    )


if __name__ == "__main__":
    flow_zpod_destroy(
        zpod_id=3,
        zpod_name="abc",
    )
