import json
from pathlib import Path


def get_component(filename: str) -> dict:
    if not Path(filename).exists():
        raise ValueError("The specified file do not exists")
    with open(filename, "r") as f:
        return json.load(f)
