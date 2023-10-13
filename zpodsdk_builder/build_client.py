import argparse
import pkgutil

MAIN_TEMPLATE = """\
from functools import cache

from {package_name} import Client

class {class_name}:
    def __init__(
        self,
        base_url,
        token,
        raise_on_unexpected_status=True,
    ):
        self._client = Client(
            base_url=base_url,
            headers=dict(access_token=token),
            raise_on_unexpected_status=raise_on_unexpected_status,
        )
"""

METHOD_TEMPLATE = """\
    @property
    @cache
    def {module_name}(self):
        from {package_name}.api.{tag_name} import {module_name}

        return {module_name}.{endpoint_name}(self._client)
"""


def build_methods(package_name, class_name):
    method_definitions = []
    base = f"{package_name}/api"
    for _, tag_name, _ in pkgutil.iter_modules([base]):
        method_definitions.extend(
            METHOD_TEMPLATE.format(
                class_name=class_name,
                module_name=module_name,
                endpoint_name=module_name.replace("_", " ").title().replace(" ", ""),
                package_name=package_name,
                tag_name=tag_name or "default",
            )
            for _, module_name, _ in pkgutil.iter_modules([f"{base}/{tag_name}"])
        )
    return sorted(method_definitions)


def build(package_name, class_name="SdkClient"):
    return "\n".join(
        [
            MAIN_TEMPLATE.format(
                package_name=package_name,
                class_name=class_name,
            ),
            *build_methods(package_name, class_name),
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client Builder")
    parser.add_argument("package_name", help="Package Name")
    parser.add_argument("--class_name", help="Class Name")
    args = vars(parser.parse_args())

    package_name = args["package_name"]
    class_name = args["class_name"]
    if not class_name:
        sections = package_name.split("_")
        class_name = "".join([*map(str.title, sections), "Client"])

    output = build(package_name=package_name, class_name=class_name)
    with open(f"{package_name}/{package_name}_client.py", "w+") as f:
        f.write(output)
