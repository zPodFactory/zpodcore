"""Naming helpers - every resource the suite creates gets a name matching
`<prefix><kind>`, so the cleanup sweep can find (and a human can recognize)
anything this suite is responsible for.

Deliberately short and free of timestamps/random suffixes - the suite runs
one session at a time and cleans up after itself (see
`_sweep_before_session`/`_sweep_after_session` in conftest.py), and zpod
names in particular end up in real DNS hostnames, where a
`e2e-smoke-20260702080047-65212c`-style name is unreadable noise. Callers
that need several distinct instances (e.g. the concurrency batch) pass
their own short numeric suffix in `kind` (e.g. `namer(f"smoke-{i:02d}")` ->
`e2e-smoke-01`), rather than `Namer` inventing one.
"""

# RFC 2606 reserved domains like .invalid/.test/.example are rejected
# outright by the API's email validator ("special-use or reserved name") -
# discovered against a live server. Use a subdomain
# of a real domain instead for every throwaway user this suite creates.
E2E_EMAIL_DOMAIN = "e2e.zpodfactory.io"


class Namer:
    """Callable name generator - prefixes every name so the cleanup sweep can find it."""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, kind: str) -> str:
        return f"{self.prefix}{kind}"
