from zpodcommon import models as M
from zpodengine.lib import database


def execute_config_script(
    zpod_id: int,
) -> None:
    """
    Sample config script

    Args:
        zpod_id: The zPod ID
    """

    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        print(f"This is just a sample config script doing nothing for zPod {zpod.name}")

