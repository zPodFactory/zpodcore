from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodComponentStatus
from zpodengine.lib import database
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
    set_zpod_component_status,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_config_scripts(*, zpod_component_id: int):
    set_zpod_component_status(zpod_component_id, ZpodComponentStatus.CONFIG_SCRIPTS)
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)
        component = zpod_component.component
        zpod = zpod_component.zpod
        features = zpod.features
        if features:
            if isinstance(features, dict):
                config_scripts = features.get("config-scripts", [])
                if isinstance(config_scripts, list):
                    if config_scripts:
                        for config_script in config_scripts:
                            print(f"Asked to execute config script {config_script}/zpod_component_add_{component.component_name}.py for zPod {zpod.name} for {component.component_name}")
                            # Import dynamically the config script module if it exists
                            try:
                                module_name = f"zpodengine.config_scripts.{config_script}.zpod_component_add_{component.component_name}"
                                module = __import__(module_name, fromlist=['execute_config_script'])

                                print(f"Executing config script {config_script}/zpod_component_add_{component.component_name}.py for zPod {zpod.name} for {component.component_name}")
                                module.execute_config_script(zpod_component_id=zpod_component_id)
                            except ImportError:
                                print(f"No config script {config_script}/zpod_component_add_{component.component_name}.py found for zPod {zpod.name} for {component.component_name}")
                                pass
                    else:
                        print(f"config-scripts is empty for zPod {zpod.name}")
                else:
                    print(f"config-scripts is not a list for zPod {zpod.name}")
            else:
                print(f"features is not a dict for zPod {zpod.name}")
        else:
            print(f"features is empty for zPod {zpod.name}")
