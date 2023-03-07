import json
from pathlib import Path


def get_component(filename: str) -> dict:
    if not Path(filename).exists():
        raise ValueError(f"The specified file {filename} does not exist")
    with open(filename, "r") as f:
        return json.load(f)
