from prefect import task

from zpodcommon import models as M
from zpodcommon.enums import ZpodStatus
from zpodengine.lib import database


@task
def zpod_destroy_config_scripts(*, zpod_id: int):
    with database.get_session_ctx() as session:
        zpod = session.get(M.Zpod, zpod_id)
        zpod.status = ZpodStatus.CONFIG_SCRIPTS
        session.add(zpod)
        session.commit()

        features = zpod.features
        if features:
            if isinstance(features, dict):
                config_scripts = features.get("config-scripts", [])
                if isinstance(config_scripts, list):
                    if config_scripts:
                        for config_script in config_scripts:
                            print(f"Asked to execute config script {config_script}/zpod_destroy.py for zPod {zpod.name}")
                            # Import dynamically the config script module if it exists
                            try:
                                module_name = f"zpodengine.config_scripts.{config_script}.zpod_destroy"
                                module = __import__(module_name, fromlist=['execute_config_script'])

                                print(f"Executing config script {config_script}/zpod_destroy.py for zPod {zpod.name}")
                                module.execute_config_script(zpod_id=zpod_id)
                            except ImportError:
                                print(f"No config script {config_script}/zpod_destroy.py found for zPod {zpod.name}")
                                pass
                    else:
                        print(f"config-scripts is empty for zPod {zpod.name}")
                else:
                    print(f"config-scripts is not a list for zPod {zpod.name}")
            else:
                print(f"features is not a dict for zPod {zpod.name}")
        else:
            print(f"features is empty for zPod {zpod.name}")
