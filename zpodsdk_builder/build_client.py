import argparse
import os

MAIN_TEMPLATE = """\
import importlib
from functools import cache, partial

from {package_name} import AuthenticatedClient, Client
from {package_name}.api.token import token
from {package_name}.models import BodyTokenTokenPost


class {class_name}:
    def __init__(self, base_url):
        self.client = Client(base_url=base_url)

    def load_mod(self, mod):
        mod = importlib.import_module(mod)
        for attr in ("asyncio", "asyncio_detailed", "sync", "sync_detailed"):
            if method := getattr(mod, attr):
                setattr(mod, attr, partial(method, client=self.client))
        return mod
"""

METHOD_TEMPLATE = """\
    @property
    @cache
    def {module_name}(self):
        return self.load_mod('{package_name}.api.{api_name}.{module_name}')
"""


def build_methods(package_name):
    out = []
    api_path = f"{package_name}/api"
    for api_item in os.scandir(path=api_path):
        if api_item.is_dir() and not api_item.name.startswith("__"):
            api_name = api_item.name
            for module_item in os.scandir(path=f"{api_path}/{api_name}"):
                if module_item.is_file() and not module_item.name.startswith("__"):
                    # Strip ".py"
                    module_name = module_item.name[0:-3]
                    out.append(
                        METHOD_TEMPLATE.format(
                            package_name=package_name,
                            api_name=api_name,
                            module_name=module_name,
                        )
                    )
    return "\n".join(sorted(out))


def build(package_name, class_name="SdkClient"):
    return "\n".join(
        [
            MAIN_TEMPLATE.format(package_name=package_name, class_name=class_name),
            build_methods(package_name),
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
    f = open(f"{package_name}/{package_name}_client.py", "w+")
    f.write(output)
    f.close()
