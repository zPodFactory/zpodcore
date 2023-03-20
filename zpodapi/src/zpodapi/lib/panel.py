import contextlib
import json
import logging
from functools import partial

from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from zpodapi import settings

logger = logging.getLogger(__name__)
MyPretty = partial(Pretty, indent_size=2)


def print_panel(output, title=None):
    rprint(Panel(output, title=title, title_align="left"))


def print_panel_obj(obj, title=None):
    print_panel(MyPretty(obj), title=title)


def log_obj(obj, title):
    if settings.DEV_MODE:
        print_panel_obj(format_obj(obj), title)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s %s", title or "", format_obj(obj))


def format_obj(obj):
    if type(obj) == bytes:
        obj = obj.decode("utf-8")

    if type(obj) == str:
        with contextlib.suppress(json.JSONDecodeError):
            obj = json.loads(obj)
    return obj
