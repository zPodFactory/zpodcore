import json


def get_component_uid(filename: str) -> str:
    with open(filename, "r") as f:
        component = json.load(f)
        return f"{component['component_name']}-{component['component_version']}"
