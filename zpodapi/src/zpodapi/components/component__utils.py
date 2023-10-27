import json
from pathlib import Path


def get_component(jsonfile: str) -> dict:
    if not Path(jsonfile).exists():
        raise ValueError(f"The specified file {jsonfile} does not exist")
    with open(jsonfile) as f:
        return json.load(f)
