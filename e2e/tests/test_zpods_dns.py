"""zPod DNS entry management.

`zcli zpod dns list` has no `--json` flag, so these tests read DNS state
back through the SDK client - the actions themselves (add/update/remove)
go through the CLI.
"""

import pytest

from e2e.insight import Beat, Insight

DNS_HOST_ID = 60

# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests below, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_dns_add_entry_resolves": Insight(
        why="An API response saying a DNS entry exists is a claim, not a fact - the only real "
            "proof is a resolver actually answering the query.",
        reasoning="dnsmasq (the resolver behind zpodcore) reads its config from what the API "
                  "writes, but reload/propagation is a real step in between - if the suite trusted "
                  "the API's own view of DNS state, a config-write bug that never reaches dnsmasq "
                  "would go completely unnoticed.",
        expected="After `zpod dns add`, the hostname shows up in the API's own list AND a live DNS "
                 "query against the real resolver returns an IP.",
        beats=[
            Beat("zpod dns add", "via zcli", state="0", color="pass"),
            Beat("API's own list", "zpods_dns_get_all", state="present", color="pass", tag="WHAT THE API SAYS"),
            Beat("real DNS query", "against E2E_DNS_RESOLVER", state="resolves", color="pass", tag="THE ACTUAL PROOF"),
        ],
    ),
    "test_dns_remove_entry_stops_resolving": Insight(
        why="A stale DNS record pointing at nothing is worse than no record at all - removal has "
            "to actually take effect, not just disappear from an API list.",
        reasoning="Same reasoning as the add test in reverse: proving removal means proving the "
                  "resolver itself stops answering, not just that the API forgot about the row.",
        expected="Immediately after `zpod dns remove`, the same hostname that resolved a moment "
                 "ago now returns NXDOMAIN from a real query.",
        beats=[
            Beat("hostname resolves", "confirmed before removal", state="resolves", color="pass", tag="BEFORE"),
            Beat("zpod dns remove", "via zcli", state="0", color="pass"),
            Beat("same hostname, requeried", "against the real resolver", state="NXDOMAIN", color="pass", tag="AFTER"),
        ],
    ),
    "test_dns_add_requires_exactly_one_of_ip_or_host_id": Insight(
        why="'Exactly one of A or B' is a business rule, not something a JSON schema can express "
            "on its own - it has to be enforced in application code, which means it can be gotten "
            "wrong in a way schema validation wouldn't catch.",
        reasoning="dns_add's ip/host_id exclusivity is a manual `if` check in "
                  "zpod_dns__routes.py, not a pydantic field constraint - so it surfaces as a plain "
                  "400 with a text detail message, not FastAPI's usual 422 for a schema violation. "
                  "Getting the status code right here is the whole point of the test.",
        expected="Both invalid shapes (both set, neither set) come back 400, never 422.",
        beats=[
            Beat("both ip and host_id set", "ambiguous request", state="400", color="pass", tag="MANUAL CHECK, NOT SCHEMA"),
            Beat("neither set", "underspecified request", state="400", color="pass"),
        ],
    ),
}


@pytest.fixture
def active_zpod(zcli_as, namer, zcore_profile, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, keep_resources):
    """A deployed, ACTIVE minimal zcore zpod - torn down at teardown. Duplicated from test_zpods.py's
    fixture of the same name (module-local fixtures aren't shared across files by default)."""
    runner = zcli_as("superadmin")
    zpod_name = namer("zpod-dns")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", zcore_profile,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"setup deploy failed:\n{result.stdout}\n{result.stderr}"

    yield zpod_name

    if not keep_resources:
        runner("zpod", "destroy", zpod_name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
        except Exception:
            pass


def _zpod_domain(superadmin_client, zpod_name: str) -> str:
    return superadmin_client.zpods_get.sync(id=f"name={zpod_name}").domain


def test_dns_add_entry_resolves(zcli_as, active_zpod, superadmin_client, wait_dns_resolves):
    """Adding a DNS entry to a zpod makes it actually resolve, not just appear in the API."""
    domain = _zpod_domain(superadmin_client, active_zpod)
    hostname = "dns-add-test"
    fqdn = f"{hostname}.{domain}"

    runner = zcli_as("superadmin")
    result = runner("zpod", "dns", "add", active_zpod, "--hostname", hostname, "--host-id", str(DNS_HOST_ID))
    assert result.returncode == 0, f"zpod dns add failed:\n{result.stderr}"

    entries = superadmin_client.zpods_dns_get_all.sync(id=f"name={active_zpod}") or []
    assert any(e.hostname == hostname for e in entries), f"expected {hostname} in zpod dns list after add"

    resolved_ip = wait_dns_resolves(fqdn)
    assert resolved_ip, f"expected {fqdn} to resolve via DNS after adding it"


def test_dns_update_entry_changes_resolution(zcli_as, active_zpod, superadmin_client, wait_dns_resolves):
    """Updating a DNS entry's IP is reflected in a fresh DNS query."""
    domain = _zpod_domain(superadmin_client, active_zpod)
    hostname = "dns-update-test"
    fqdn = f"{hostname}.{domain}"

    runner = zcli_as("superadmin")
    runner("zpod", "dns", "add", active_zpod, "--hostname", hostname, "--host-id", str(DNS_HOST_ID + 1))
    first_ip = wait_dns_resolves(fqdn)

    result = runner(
        "zpod", "dns", "update", active_zpod,
        "--hostname", hostname, "--ip", first_ip,
        "--newhost-id", str(DNS_HOST_ID + 2),
        "--yes",
    )
    assert result.returncode == 0, f"zpod dns update failed:\n{result.stderr}"

    # Re-resolve and confirm it still resolves, to a new IP.
    second_ip = wait_dns_resolves(fqdn)
    assert second_ip != first_ip, f"expected {fqdn} to resolve to a new IP after update, still {first_ip}"


def test_dns_remove_entry_stops_resolving(zcli_as, active_zpod, superadmin_client, wait_dns_resolves, wait_dns_nxdomain):
    """Removing a DNS entry makes it stop resolving."""
    domain = _zpod_domain(superadmin_client, active_zpod)
    hostname = "dns-remove-test"
    fqdn = f"{hostname}.{domain}"

    runner = zcli_as("superadmin")
    runner("zpod", "dns", "add", active_zpod, "--hostname", hostname, "--host-id", str(DNS_HOST_ID + 3))
    resolved_ip = wait_dns_resolves(fqdn)

    result = runner("zpod", "dns", "remove", active_zpod, "--ip", resolved_ip, "--hostname", hostname, "--yes")
    assert result.returncode == 0, f"zpod dns remove failed:\n{result.stderr}"

    wait_dns_nxdomain(fqdn)


def test_dns_add_requires_exactly_one_of_ip_or_host_id(superadmin_client, active_zpod, api_check):
    """The API rejects a DNS create with both ip and host_id, or neither - exercised via the SDK
    since this is a validation edge case zcli doesn't have a direct flag combination for.

    This is a manual application-level check in zpod_dns__routes.py::dns_add
    (not pydantic schema validation), so it's a 400 with a plain-text
    detail message, not FastAPI's usual 422 for schema violations.
    """
    from zpodsdk.errors import UnexpectedStatus
    from zpodsdk.models.zpod_dns_create import ZpodDnsCreate

    with pytest.raises(UnexpectedStatus) as exc_info:
        superadmin_client.zpods_dns_add.sync(
            id=f"name={active_zpod}",
            body=ZpodDnsCreate(hostname="both-set", ip="10.0.0.99", host_id=99),
        )
    api_check(
        "POST", "/zpods/{id}/dns", "DNS create with both ip AND host_id set",
        expected=400, actual=exc_info.value.status_code,
        note="manual HTTPException in dns_add, not pydantic schema validation - hence 400, not 422",
    )
    assert exc_info.value.status_code == 400, f"expected 400 for both ip+host_id set, got {exc_info.value.status_code}"

    with pytest.raises(UnexpectedStatus) as exc_info:
        superadmin_client.zpods_dns_add.sync(
            id=f"name={active_zpod}",
            body=ZpodDnsCreate(hostname="neither-set"),
        )
    api_check(
        "POST", "/zpods/{id}/dns", "DNS create with neither ip nor host_id set",
        expected=400, actual=exc_info.value.status_code,
    )
    assert exc_info.value.status_code == 400, f"expected 400 for neither ip nor host_id set, got {exc_info.value.status_code}"
