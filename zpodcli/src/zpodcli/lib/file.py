import json
from pathlib import Path

import yaml

from zpodcli.lib.utils import exit_with_error


def load_json_or_yaml_file(path: Path):
    extension = path.suffix

    if not path.exists():
        exit_with_error(f"File not found: {path}")

    with path.open() as f:
        if extension in (".yaml", ".yml"):
            return yaml.safe_load(f)
        elif extension == ".json":
            try:
                return json.load(f)
            except json.JSONDecodeError:
                exit_with_error("The provided JSON was invalid")
        else:
            exit_with_error(f"Invalid extension: {extension}")
