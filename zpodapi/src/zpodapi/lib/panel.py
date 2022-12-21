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
        print_panel_obj(obj, title)
    logger.debug(f"{title or ''} {obj}")
