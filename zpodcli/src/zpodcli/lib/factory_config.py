import configparser
from functools import cached_property
from pathlib import Path

import typer
from rich import print

from zpodcli.lib.global_flags import GLOBAL_FLAGS
from zpodcli.lib.utils import exit_with_error


class FactoryConfig:
    def __init__(self):
        app_dir = typer.get_app_dir("zcli")
        app_dir_path = Path(app_dir)
        app_dir_path.mkdir(parents=True, exist_ok=True)
        config_path = Path(app_dir) / ".zclirc"

        if not config_path.is_file():
            with open(config_path, "w"):
                pass

        self.config_file = config_path
        self.config = self.load()
        self.cleanup()

    def load(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file)
        except configparser.Error as e:
            print(f"Error reading config file: {e}")
        return config

    def cleanup(self):
        changed = False
        hasactive = False
        factory_names = self.config.sections()
        if not factory_names:
            return

        for factory_name in factory_names:
            factory = self.config[factory_name]
            if "active" not in factory:
                factory["active"] = "False"
                changed = True
            elif factory.getboolean("active"):
                hasactive = True
        if not hasactive:
            factory = self.config[factory_names[0]]
            factory["active"] = "True"
            changed = True
        if changed:
            self.write()

    @cached_property
    def factory(self):
        if GLOBAL_FLAGS["factory"]:
            return self.config[GLOBAL_FLAGS["factory"]]

        factory_names = self.config.sections()
        for factory_name in factory_names:
            factory = self.config[factory_name]
            if factory.getboolean("active"):
                return self.config[factory_name]

        exit_with_error(
            "Please connect to a zPodFactory Server first using the following command:\n\n"
            "    zcli factory add --name <xxx> --server <xxx> --token <xxx>\n"
        )

    def setactive(self, name):
        for factory_name in self.config.sections():
            factory = self.config[factory_name]
            factory["active"] = str(factory_name == name)

    def write(self):
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)
