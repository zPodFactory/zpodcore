#
# Quick App Config manager
#

import configparser
import contextlib
from pathlib import Path

import typer


class config:
    section: str = "zpodmanager"
    config_file: Path = None

    def __init__(self):
        app_dir = typer.get_app_dir("zcli")
        app_dir_path = Path(app_dir)
        app_dir_path.mkdir(parents=True, exist_ok=True)
        config_path = Path(app_dir) / ".zclirc"

        if not config_path.is_file():
            with open(config_path, "w"):
                pass

        self.config_file = config_path

    def load(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file)

        except configparser.Error as e:
            print(f"Error reading config file: {e}")
        return config

    def setup(self, server, token):
        config = self.load()

        with contextlib.suppress(configparser.DuplicateSectionError):
            config.add_section(self.section)

        config.set(self.section, "zpod_api_url", server)
        config.set(self.section, "zpod_api_token", token)
        with open(self.config_file, "w") as configfile:
            config.write(configfile)

    def get(self, option):
        config = self.load()
        return config.get(self.section, option)

    def ismissing(self):
        config = self.load()
        try:
            config[self.section]
        except KeyError:
            return True
        return False
