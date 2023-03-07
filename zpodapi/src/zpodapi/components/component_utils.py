import json
<<<<<<< HEAD
from pathlib import Path


def get_component(filename: str) -> dict:
    if not Path(filename).exists():
        raise ValueError("The specified file do not exists")
    with open(filename, "r") as f:
        return json.load(f)
=======


def get_component_uid(filename: str) -> str:
    with open(filename, "r") as f:
        component = json.load(f)
        return f"{component['component_name']}-{component['component_version']}"
>>>>>>> main
