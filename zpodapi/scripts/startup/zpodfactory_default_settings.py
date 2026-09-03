"""Single source of truth for zpodfactory's default Settings rows.

Both `zpodfactory_load_initial_data.py` (fresh install: creates the initial
superuser and seeds every default setting) and
`zpodfactory_load_default_settings.py` (every startup: backfills any setting
a newer code version introduced) read from this list. Neither script ever
overwrites a setting that already exists, so an admin's customized value is
never touched -- this list only describes what SHOULD exist, not what the
value must be going forward.

`value` may be a plain string or a zero-arg callable, evaluated at the point
of creation (not at import time) for values that depend on runtime config.
"""

from zpodapi import settings


def _default_host() -> str:
    # TODO: We are in a docker container here, this will not work.
    return settings.HOST


DEFAULT_SETTINGS = [
    {
        "name": "zpodfactory_host",
        "description": "zpodfactory host address (NTP, ISO Datastore, etc)",
        "value": _default_host,
    },
    {
        "name": "zpodfactory_debug_level",
        "description": "Set debug verbosity level on zPodfactory",
        "value": "INFO",
    },
    {
        "name": "zpodfactory_default_domain",
        "description": "Default domain for all zPods",
        "value": "zpodfactory.io",
    },
    {
        "name": "zpodfactory_broadcom_download_token",
        "description": "Broadcom Support Portal Generated Download Token",
        "value": "",
    },
    {
        "name": "zpodfactory_ssh_key",
        "description": "Public SSH Key to be pushed on zPod components",
        "value": "",
    },
    {
        "name": "zpodfactory_fqdn_reserved_chars",
        "description": (
            "Characters reserved from the 64-char Linux kernel hostname "
            "limit when validating zPod component FQDN length at creation"
        ),
        "value": "8",
    },
    {
        "name": "ff_esxi_hostname_is_fqdn",
        "description": "William Lam VMware ESXi OVA Templates support",
        "value": "true",
    },
    {
        "name": "ff_endpoint_ova_staging",
        "description": (
            "Stage L1 OVAs as templates and clone per deployment "
            "(Experimental) - Faster & optimized flow when deploying many "
            "zPods"
        ),
        "value": "false",
    },
    {
        "name": "ff_reuse_zpod_password",
        "description": (
            "Preserve password on same-name zPod redeploy so browsers and "
            "password-managers entries don't need updating. Great for "
            "testing/QA/validations use cases"
        ),
        "value": "false",
    },
]
