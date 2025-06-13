from zpodcommon import models as M
from zpodengine.lib import database


def execute_config_script(
    zpod_component_id: int,
) -> None:
    """
    Sample config script

    Args:
        zpod_component_id: The zPod component ID
    """

    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)
        zpod = zpod_component.zpod
        print(f"This is just a sample config script doing nothing for zPod {zpod.name} and zPod component {zpod_component.component.component_name}")
