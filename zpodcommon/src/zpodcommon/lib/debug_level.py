"""Cached lookup of the zpodfactory_debug_level setting.

Avoids a DB round-trip on every request: the value is re-read at most once per
TTL window, so toggling the setting in the DB takes effect within ~TTL seconds
with no container restart.
"""

import time

# The setting is re-read from the DB at most once per this many seconds.
_TTL_SECONDS = 10.0

_cache = {"debug": False, "checked_at": 0.0}


def debug_enabled() -> bool:
    """True when zpodfactory_debug_level is set to DEBUG.

    TTL-cached (~10s). On any error (DB unreachable, missing value) the last
    known-good result is kept, defaulting to False (INFO).
    """
    now = time.monotonic()
    if now - _cache["checked_at"] >= _TTL_SECONDS:
        _cache["checked_at"] = now
        try:
            from zpodcommon.lib.dbutils import DBUtils

            value = DBUtils.get_setting_value("zpodfactory_debug_level")
            _cache["debug"] = (value or "INFO").strip().upper() == "DEBUG"
        except Exception:
            pass  # keep last known-good
    return _cache["debug"]
