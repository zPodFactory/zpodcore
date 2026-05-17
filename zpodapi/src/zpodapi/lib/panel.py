import contextlib
import json
from functools import partial

from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

# Long individual string values are abbreviated to keep panels readable.
MAX_STRING_CHARS = 2048
# A list body larger than this many raw chars is summarised; smaller responses
# render in full.
SUMMARISE_THRESHOLD = 16384
# When a large list body is summarised, show at most this many elements.
MAX_LIST_ITEMS = 10

MyPretty = partial(Pretty, indent_size=2, max_string=MAX_STRING_CHARS)


def print_panel(output, title=None):
    rprint(Panel(output, title=title, title_align="left"))


def print_panel_obj(obj, title=None):
    print_panel(MyPretty(obj), title=title)


def log_obj(obj, title):
    """Rich-print a request/response body panel.

    Call only when DEBUG logging is enabled (RouteLogger gates on
    debug_enabled()). format_obj() decodes/parses the body, summarises large
    list bodies, and replaces binary payloads with a placeholder.
    """
    print_panel_obj(format_obj(obj), title)


def _summarize_value(value):
    """Collapse a nested collection to a one-line size hint."""
    if isinstance(value, dict):
        return f"<dict: {len(value)} keys>"
    if isinstance(value, list):
        return f"<list: {len(value)} items>"
    return value


def _summarize_item(item):
    """Reduce one list element to a scannable form.

    Keeps every key (so the shape stays visible) but collapses nested dict/list
    values to a compact size hint, so a large list body stays readable.
    """
    if not isinstance(item, dict):
        return item
    return {key: _summarize_value(value) for key, value in item.items()}


def format_obj(obj):
    """Prepare a request/response body for display.

    Bytes are utf-8 decoded (binary -> placeholder) and JSON is parsed so it
    renders as a pretty tree. Small bodies render in full; a large list body
    (e.g. GET /zpods, GET /components) is summarised — each element reduced to
    its scalar fields with nested collections collapsed to a size hint, and
    only the first MAX_LIST_ITEMS shown, the rest noted as truncated.
    """
    if isinstance(obj, bytes):
        try:
            obj = obj.decode("utf-8")
        except UnicodeDecodeError:
            return f"<{len(obj)} bytes of binary data>"

    # Only large bodies are summarised; small responses render in full.
    large = isinstance(obj, str) and len(obj) > SUMMARISE_THRESHOLD

    if isinstance(obj, str):
        with contextlib.suppress(json.JSONDecodeError):
            obj = json.loads(obj)

    if large and isinstance(obj, list):
        items = [_summarize_item(item) for item in obj[:MAX_LIST_ITEMS]]
        hidden = len(obj) - len(items)
        if hidden:
            items.append(f"... [{hidden} elements truncated] ...")
        return items

    return obj
