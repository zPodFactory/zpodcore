"""The free-space floor of a datastore (D11): every workflow that consumes space on
a datastore checks it first, so it fails before creating anything."""

from prefect import get_run_logger
from pyVmomi import vim

from zpodcommon.lib.dbutils import DBUtils
from zpodcommon.lib.vmware import vCenter

GIB = 1024**3
DEFAULT_MIN_FREE_PCT = 15


class DatastoreFloorError(Exception):
    pass


def min_free_pct() -> int:
    value = DBUtils.get_setting_value("zpodfactory_datastore_min_free_pct")
    try:
        return int(value)
    except (TypeError, ValueError):
        return DEFAULT_MIN_FREE_PCT


def check_datastore_floor(ds: vim.Datastore, needed_gib: int, what: str) -> None:
    """Refuse when the datastore would have less than the floor free after `what`
    takes `needed_gib` GiB (the full size, thin or not: a thin disk can fill).

    Hard for everyone, superadmin included. One log line either way.
    """
    logger = get_run_logger()
    floor = min_free_pct()
    capacity, free = vCenter.datastore_space(ds)
    left = free - needed_gib * GIB
    line = (
        f"datastore {ds.name}: {free // GIB} GiB free of {capacity // GIB} GiB "
        f"({free / capacity:.1%}); +{needed_gib} GiB for {what} "
        f"{'leaves' if left >= 0 else 'would leave'} {left // GIB} GiB "
        f"({left / capacity:.1%})"
    )
    if left * 100 < capacity * floor:
        logger.error(f"{line} < floor {floor}%: refused")
        raise DatastoreFloorError(
            f"datastore {ds.name}: {free // GIB} GiB free of {capacity // GIB} GiB; "
            f"{needed_gib} GiB more would leave {left // GIB} GiB "
            f"({left / capacity:.1%}), under the floor of {floor}% "
            "(zpodfactory_datastore_min_free_pct)"
        )
    logger.info(f"{line} ≥ floor {floor}%: ok")
