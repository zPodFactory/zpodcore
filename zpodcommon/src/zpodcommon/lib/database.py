# flake8: noqa
# type: ignore[reportMissingImports]


# Load proper database
try:
    from zpodapi.lib.database import *
except ModuleNotFoundError:
    from zpodengine.lib.database import *
