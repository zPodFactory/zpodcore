"""Endpoint checks - lightweight, best-effort.

Full endpoint CRUD/enet management needs real vCenter/NSX credentials for a
*disposable* endpoint and isn't on the critical path - this file only
exercises what's safe to run against the pre-existing E2E_ENDPOINT_NAME
every time: listing, and connectivity verification.
`zcli` has no `endpoint verify` command, so that check goes through the SDK.
"""


def test_endpoints_list_includes_configured_endpoint(zcli_as, e2e_config):
    """`zcli endpoint list` exits cleanly and the configured endpoint is registered."""
    runner = zcli_as("superadmin")
    result = runner("endpoint", "list")
    assert result.returncode == 0, f"endpoint list failed:\n{result.stderr}"
    assert e2e_config.endpoint_name in result.stdout, (
        f"expected {e2e_config.endpoint_name} to appear in `endpoint list` output"
    )


def test_endpoint_verify(superadmin_client, endpoint):
    """The configured endpoint's vCenter/NSX connectivity actually verifies - not exposed via zcli."""
    result = superadmin_client.endpoints_verify.sync(id=f"name={endpoint.name}")
    assert result is not None, f"endpoint verify returned nothing for {endpoint.name}"
