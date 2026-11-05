import functools
import time
from pathlib import Path

import pytest

from e2e import cli, dns, polling
from e2e import profiles as profiles_lib
from e2e.cleanup import delete_unused_profiles, sweep_e2e_resources
from e2e.client_factory import build_client
from e2e.config import ConfigError, load_settings
from e2e.console import banner, console
from e2e.naming import E2E_EMAIL_DOMAIN, Namer
from e2e.prefect_diag import PrefectDiagnostics
from e2e.profiles import profile_body
from e2e.report import recorder
from e2e.zssh import ZpodSsh, public_key_of

PROFILES_DIR = Path(__file__).parent / "fixtures" / "profiles"

diag_hint_key = pytest.StashKey[str]()


# --------------------------------------------------------------------------
# Collection-time parametrization: profile files and upload-source files.
# Kept resilient to missing config so `pytest --collect-only` never errors
# out just because .env isn't filled in yet - individual tests that need
# real config fail informatively via the preflight fixture at run time.
# --------------------------------------------------------------------------


def pytest_generate_tests(metafunc):
    if "profile_file" in metafunc.fixturenames:
        files = profiles_lib.discover_profile_files(PROFILES_DIR)
        metafunc.parametrize("profile_file", files, ids=[p.stem for p in files])

    if "upload_file" in metafunc.fixturenames:
        files = []
        try:
            cfg = load_settings()
            download_dir = Path(cfg.download_source_dir).expanduser()
            if download_dir.is_dir():
                files = sorted(p for p in download_dir.iterdir() if p.is_file())
        except (ConfigError, OSError):
            files = []
        if not files:
            files = [pytest.param(None, marks=pytest.mark.skip(
                reason="no readable files in E2E_DOWNLOAD_SOURCE_DIR (default ~/downloads)"), id="no-files")]
            metafunc.parametrize("upload_file", files)
        else:
            metafunc.parametrize("upload_file", files, ids=[p.name for p in files])


def pytest_configure(config):
    console.rule("[bold]e2e[/bold] - live zpodcore end-to-end suite")


def pytest_sessionstart(session):
    recorder.begin_session({})


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def e2e_config():
    try:
        return load_settings()
    except ConfigError as e:
        pytest.exit(str(e), returncode=1)


@pytest.fixture(scope="session")
def namer(e2e_config):
    return Namer(prefix=e2e_config.resource_prefix)


# --------------------------------------------------------------------------
# SDK clients
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def superadmin_client(e2e_config):
    return build_client(e2e_config.api_base_url, e2e_config.superadmin_token)


@pytest.fixture(scope="session", autouse=True)
def _session_preflight(e2e_config, superadmin_client):
    """Fail the whole session fast, with one clear message, instead of every
    test failing individually with a connection/auth error."""
    recorder.meta.update({"api_base_url": e2e_config.api_base_url, "endpoint_name": e2e_config.endpoint_name})
    try:
        superadmin_client.root_root.sync()
    except Exception as e:
        pytest.exit(f"e2e preflight: API not reachable at {e2e_config.api_base_url}: {e}", returncode=1)

    try:
        me = superadmin_client.users_get_me.sync()
    except Exception as e:
        pytest.exit(f"e2e preflight: E2E_SUPERADMIN_TOKEN did not authenticate: {e}", returncode=1)
    if not me.superadmin:
        pytest.exit(
            f"e2e preflight: E2E_SUPERADMIN_TOKEN authenticates as '{me.username}' but is not a superadmin",
            returncode=1,
        )

    try:
        endpoints = superadmin_client.endpoints_get_all.sync() or []
    except Exception as e:
        pytest.exit(f"e2e preflight: could not list endpoints: {e}", returncode=1)
    match = next((e for e in endpoints if e.name == e2e_config.endpoint_name), None)
    if not match:
        pytest.exit(f"e2e preflight: no endpoint named '{e2e_config.endpoint_name}' found", returncode=1)


@pytest.fixture(scope="session")
def endpoint(_session_preflight, superadmin_client, e2e_config):
    endpoints = superadmin_client.endpoints_get_all.sync() or []
    return next(e for e in endpoints if e.name == e2e_config.endpoint_name)


# --------------------------------------------------------------------------
# Sweep - runs before (clean up any previous crashed run) and after
# (unless E2E_KEEP_RESOURCES) every session.
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keep_resources(e2e_config):
    return e2e_config.keep_resources


@pytest.fixture(scope="session", autouse=True)
def _sweep_before_session(_session_preflight, superadmin_client, e2e_config):
    removed = sweep_e2e_resources(superadmin_client, e2e_config.resource_prefix, keep_failed=e2e_config.keep_failed_resources)
    # Resource names are fixed, so a zPod left in place by a previous run
    # (kept for inspection, or still deploying) collides with the zPod and
    # profile this run creates under the same name. Stop with the reason
    # instead of failing every fixture on a name conflict.
    left = [
        name
        for key, names in removed.items()
        if key.startswith("zpods (")
        for name in names
    ]
    if left:
        pytest.exit(
            f"e2e: zPods from a previous run are still on the stack: {', '.join(left)}. "
            "Inspect them if needed, then run `uv run python scripts/cleanup.py --include-failed` "
            "(or `zcli zpod destroy <name>`) and start again.",
            returncode=1,
        )


@pytest.fixture(scope="session", autouse=True)
def _sweep_after_session(
    superadmin_client, e2e_config, keep_resources, namer, endpoint, zcore_profile_items, poll_zpod_status, poll_zpod_deleted,
):
    yield
    # Report generation runs *before* the cleanup sweep, not after - by
    # session end almost everything the actual test run created has
    # already torn itself down at its own test/fixture scope anyway, so
    # ordering this after the sweep would just mean showcasing an empty
    # system either way. What actually matters is capturing whatever's
    # real (see _generate_report's own throwaway zpod) before wiping it.
    try:
        _generate_report(superadmin_client, e2e_config, namer, endpoint, zcore_profile_items, poll_zpod_status, poll_zpod_deleted)
    except Exception as e:
        console.print(f"[yellow]e2e report generation failed (non-fatal): {e}[/yellow]")
    if not keep_resources:
        sweep_e2e_resources(superadmin_client, e2e_config.resource_prefix, keep_failed=e2e_config.keep_failed_resources)


# --------------------------------------------------------------------------
# HTML report - "screenshots" via zcli's own `--output-svg`, one card per
# test with its docstring/CLI calls/Prefect flow runs, and a Gantt-style
# timeline. Uses a throwaway factory - and a throwaway zpod, deployed just
# for this - so it never depends on ordering against `_role_identities`'s
# teardown, or on anything from the actual test run still being around.
# --------------------------------------------------------------------------

# Third element is "does this have anything worth showing right now" - a
# showcase screenshot of an empty list (which is the common case once
# tests have cleaned up after themselves) isn't useful, so skip capturing
# it rather than showcase a system that looks unused. None means "always
# capture" (factory list is local CLI state, not a server-side resource
# that empties out).
SHOWCASE_COMMANDS = [
    ("zPod List", ("zpod", "list"), lambda c: bool(c.zpods_get_all.sync())),
    ("Component List", ("component", "list"), lambda c: any(x.status == "ACTIVE" for x in (c.components_get_all.sync() or []))),
    ("Setting List", ("setting", "list"), lambda c: bool(c.settings_get_all.sync())),
    ("Profile List", ("profile", "list"), lambda c: bool(c.profiles_get_all.sync())),
    ("User List", ("user", "list", "--all"), lambda c: bool(c.users_get_all.sync(all_=True))),
    ("Permission Group List", ("group", "list"), lambda c: bool(c.permission_groups_get_all.sync())),
    ("Endpoint List", ("endpoint", "list"), lambda c: bool(c.endpoints_get_all.sync())),
    ("Factory List", ("factory", "list"), None),
]


def _generate_report(
    superadmin_client, e2e_config, namer, endpoint, zcore_profile_items, poll_zpod_status, poll_zpod_deleted,
) -> None:
    from zpodsdk.models.zpod_create import ZpodCreate

    factory_name = namer("factory-report")
    cli.add_factory(factory_name, e2e_config.api_base_url, e2e_config.superadmin_token)

    # A small throwaway zpod, deployed solely so the "zPod List"/"zPod
    # Info"/"Profile List" screenshots have something real to show -
    # best-effort: if the deploy fails or times out, the rest of the
    # showcase (settings/users/groups/endpoints/factory) still captures
    # fine without it.
    profile_name = namer("profile-report")
    zpod_name = namer("zpod-report")
    showcase_zpod = None
    try:
        superadmin_client.profiles_create.sync(body=profile_body(profile_name, zcore_profile_items))
        superadmin_client.zpods_create.sync(body=ZpodCreate(name=zpod_name, endpoint_id=endpoint.id, profile=profile_name))
        poll_zpod_status(superadmin_client, f"name={zpod_name}", timeout_seconds=e2e_config.deploy_timeout_seconds)
        showcase_zpod = zpod_name
    except Exception as e:
        console.print(f"[yellow]showcase zpod deploy failed (non-fatal, skipping zpod screenshots): {e}[/yellow]")

    try:
        for label, args, has_content in SHOWCASE_COMMANDS:
            if has_content is not None and not has_content(superadmin_client):
                continue
            # zcli_run always captures its own `--output-svg` screenshot (see
            # cli.py) and moves it into report_svgs/ - reuse that instead of
            # duplicating the diff-glob logic here.
            result = cli.zcli_run(*args, factory=factory_name, check=False, timeout=60)
            if result.svg:
                recorder.log_svg(label, result.svg, svg_path=result.svg_path)

        if showcase_zpod:
            result = cli.zcli_run("zpod", "info", showcase_zpod, factory=factory_name, check=False, timeout=60)
            if result.svg:
                recorder.log_svg(f"zPod Info: {showcase_zpod}", result.svg, svg_path=result.svg_path)
    finally:
        if showcase_zpod:
            try:
                cli.zcli_run("zpod", "destroy", showcase_zpod, factory=factory_name, check=False, timeout=60)
                poll_zpod_deleted(superadmin_client, f"name={showcase_zpod}", timeout_seconds=e2e_config.deploy_timeout_seconds)
            except Exception:
                pass
        # Only once the showcase zpod is gone: if its deploy timed out it may
        # still be building, and then the session sweep removes both.
        delete_unused_profiles(
            superadmin_client, [profile_name], wait_seconds=e2e_config.deploy_timeout_seconds
        )
        cli.remove_factory(factory_name)

    recorder.meta["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report_path = Path(__file__).resolve().parents[1] / "report.html"
    recorder.render_html(report_path)
    console.print(f"[bold green]e2e report written to {report_path}[/bold green]")


# --------------------------------------------------------------------------
# Role identities: test_admin (superadmin), test_owner, test_user.
# Self-provisioned each session, registered as ephemeral zcli factories so
# CLI-driven tests can select identity via --factory.
# --------------------------------------------------------------------------

ROLE_SPECS = {
    "test_admin": {"superadmin": True},
    "test_owner": {"superadmin": False},
    "test_user": {"superadmin": False},
}


@pytest.fixture(scope="session")
def _role_identities(superadmin_client, e2e_config, namer, keep_resources):
    from zpodsdk.models.user_create import UserCreate

    identities = {}

    superadmin_factory = namer("factory-superadmin")
    cli.add_factory(superadmin_factory, e2e_config.api_base_url, e2e_config.superadmin_token)
    identities["superadmin"] = {
        "client": superadmin_client, "factory": superadmin_factory, "username": None,
        "token": e2e_config.superadmin_token,
    }

    for role, spec in ROLE_SPECS.items():
        username = namer(role.replace("_", "-"))
        user = superadmin_client.users_create.sync(
            body=UserCreate(
                username=username,
                email=f"{username}@{E2E_EMAIL_DOMAIN}",
                description=f"e2e ephemeral {role} account",
                superadmin=spec["superadmin"],
            )
        )
        token = user.api_token
        client = build_client(e2e_config.api_base_url, token)
        # zcli factory names only allow [A-Za-z0-9-] (no underscores).
        factory_name = namer(f"factory-{role.replace('_', '-')}")
        cli.add_factory(factory_name, e2e_config.api_base_url, token)
        identities[role] = {"client": client, "factory": factory_name, "username": username, "token": token}

    yield identities

    if not keep_resources:
        for role_data in identities.values():
            cli.remove_factory(role_data["factory"])
        for role in ROLE_SPECS:
            username = identities[role]["username"]
            superadmin_client.users_delete.sync(id=f"username={username}")


@pytest.fixture(scope="session")
def test_admin_client(_role_identities):
    return _role_identities["test_admin"]["client"]


@pytest.fixture(scope="session")
def test_owner_client(_role_identities):
    return _role_identities["test_owner"]["client"]


@pytest.fixture(scope="session")
def test_user_client(_role_identities):
    return _role_identities["test_user"]["client"]


@pytest.fixture(scope="session")
def zcli_as(_role_identities):
    """zcli_as("test_owner")("zpod", "list", "--json") runs a real zcli
    command as that role's ephemeral factory identity - see
    e2e.cli.RoleRunner."""

    def _runner(role: str) -> cli.RoleRunner:
        return cli.RoleRunner(factory=_role_identities[role]["factory"])

    return _runner


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def available_profile_files():
    """All profile fixture files as a plain list - for tests that need the
    whole set at once (e.g. the concurrency batch), as opposed to
    `profile_file`, which pytest_generate_tests parametrizes individual
    tests over."""
    return profiles_lib.discover_profile_files(PROFILES_DIR)


@pytest.fixture(scope="session")
def zcore_profile_items():
    zcore_path = PROFILES_DIR / "zcore.json"
    if not zcore_path.is_file():
        pytest.skip(f"no {zcore_path} fixture - drop a minimal zcore profile sample there")
    return profiles_lib.load_profile_items(zcore_path)


@pytest.fixture
def zcore_profile(superadmin_client, namer, zcore_profile_items, keep_resources):
    """Creates a throwaway Profile record from the zcore.json fixture and
    returns its name. Deletes it at teardown."""

    name = namer("profile-zcore")
    superadmin_client.profiles_create.sync(body=profile_body(name, zcore_profile_items))
    yield name
    if not keep_resources:
        try:
            superadmin_client.profiles_delete.sync(id=f"name={name}")
        except Exception:
            pass  # already deleted (e.g. by the test itself, or a blocked-then-cleared-up retry)


# --------------------------------------------------------------------------
# On-host verification: SSH into the zPods the suite deploys, with the
# factory's key (see e2e.zssh), and one shared zcore zPod for the network
# and storage modules.
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def zpod_ssh_key(_session_preflight, superadmin_client, e2e_config) -> Path:
    """The private key that logs into every zPod VM, checked against the
    server's zpodfactory_ssh_key setting once, so a mismatch fails here with
    one clear message instead of as N unexplained "Permission denied"."""
    key = e2e_config.zpod_ssh_key.expanduser()
    if not key.is_file():
        pytest.skip(f"E2E_ZPOD_SSH_KEY {key} not found - on-host checks need the factory's private key")
    settings = superadmin_client.settings_get_all.sync() or []
    server_key = next((s.value for s in settings if s.name == "zpodfactory_ssh_key"), "") or ""
    local_pub = public_key_of(key)
    assert local_pub and local_pub in server_key, (
        f"E2E_ZPOD_SSH_KEY {key} is not the key in the zpodfactory_ssh_key setting "
        f"(server has '{server_key[:40]}...', local public key '{local_pub[:40]}...'); "
        "zPod VMs only accept the setting's key"
    )
    return key


def _component_ip(client, zpod_name: str, hostname: str) -> str:
    components = client.zpods_components_get_all.sync(id=f"name={zpod_name}") or []
    match = next((c for c in components if c.hostname == hostname), None)
    assert match and match.ip, f"zPod {zpod_name} has no component '{hostname}' with an IP"
    return match.ip


@pytest.fixture(scope="session")
def zpod_ssh(zpod_ssh_key, superadmin_client):
    """zpod_ssh(zpod_name) -> ZpodSsh on that zPod's zcore; .jump(ip) for a VM behind it.
    zpod_ssh(zpod_name, hostname="zbox") for another component reachable directly."""

    def _ssh(zpod_name: str, hostname: str = "zcore") -> ZpodSsh:
        return ZpodSsh(host=_component_ip(superadmin_client, zpod_name, hostname), key_path=zpod_ssh_key)

    return _ssh


@pytest.fixture(scope="session")
def zcore_zpod(zcli_as, namer, endpoint, superadmin_client, e2e_config, poll_zpod_deleted, keep_resources):
    """One ACTIVE zcore-only zPod (E2E_ZCORE_COMPONENT_UID) shared by the
    network and storage modules - both work on zcore's own VLANs, disks and
    exports, never on each other's, so one ~3 min deploy serves both.

    Each module cleans up what it adds; the zPod itself goes at session end."""

    runner = zcli_as("superadmin")
    zpod_name = namer("zcore")
    profile_name = namer("profile-zcore-selfservice")
    superadmin_client.profiles_create.sync(
        body=profile_body(profile_name, [{"component_uid": e2e_config.zcore_component_uid}])
    )
    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", profile_name,
        "--wait", "--no-spinner",
        check=False,
        timeout=e2e_config.deploy_timeout_seconds + 60,
    )
    if result.returncode != 0:
        pytest.fail(f"shared zcore zPod deploy failed:\n{result.stdout}\n{result.stderr}")

    yield zpod_name

    if not keep_resources:
        runner("zpod", "destroy", zpod_name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
        except Exception:
            pass
        try:
            superadmin_client.profiles_delete.sync(id=f"name={profile_name}")
        except Exception:
            pass


@pytest.fixture(scope="session")
def zcore_ssh(zcore_zpod, zpod_ssh) -> ZpodSsh:
    """SSH on the shared zcore zPod's zcore, ready (key login works)."""
    zc = zpod_ssh(zcore_zpod)
    zc.wait_ready()
    return zc


# --------------------------------------------------------------------------
# Polling helpers, bound to configured timeouts.
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def poll_zpod_status(e2e_config):
    return functools.partial(
        polling.poll_zpod_status,
        timeout_seconds=e2e_config.deploy_timeout_seconds,
        interval_seconds=e2e_config.poll_interval_seconds,
    )


@pytest.fixture(scope="session")
def poll_zpod_component_status(e2e_config):
    return functools.partial(
        polling.poll_zpod_component_status,
        timeout_seconds=e2e_config.deploy_timeout_seconds,
        interval_seconds=e2e_config.poll_interval_seconds,
    )


@pytest.fixture(scope="session")
def poll_zpod_deleted(e2e_config):
    return functools.partial(
        polling.poll_zpod_deleted,
        timeout_seconds=e2e_config.deploy_timeout_seconds,
        interval_seconds=e2e_config.poll_interval_seconds,
    )


@pytest.fixture(scope="session")
def poll_library_component_download(e2e_config):
    return functools.partial(
        polling.poll_library_component_download,
        timeout_seconds=e2e_config.component_download_timeout_seconds,
        interval_seconds=e2e_config.poll_interval_seconds,
    )


# --------------------------------------------------------------------------
# DNS
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def wait_dns_resolves(e2e_config):
    return functools.partial(dns.wait_until_resolves, resolver_ip=e2e_config.dns_resolver)


@pytest.fixture(scope="session")
def wait_dns_nxdomain(e2e_config):
    return functools.partial(dns.wait_until_nxdomain, resolver_ip=e2e_config.dns_resolver)


# --------------------------------------------------------------------------
# Prefect diagnostics
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def prefect_diag(e2e_config):
    return PrefectDiagnostics(e2e_config.prefect_api_url, e2e_config.prefect_ui_url)


class DiagRecorder:
    def __init__(self, node):
        self._node = node

    def set_hint(self, text: str) -> None:
        self._node.stash[diag_hint_key] = text


@pytest.fixture
def diag(request):
    return DiagRecorder(request.node)


@pytest.fixture
def api_check(request):
    """Record a structured "expected X, got Y" request/response card for
    the HTML report - for SDK-direct calls whose whole point is a specific
    status code or response shape, where a bare pass/fail tells an
    operator nothing about what was actually being verified.

    Doesn't change control flow - the test still does its own
    `pytest.raises`/assert; this just records what happened alongside it:

        with pytest.raises(UnexpectedStatus) as exc_info:
            client.zpods_delete.sync(id=f"name={zpod}")
        api_check("DELETE", "/zpods/{id}", "zero-grant user deletes a zpod",
                  expected=404, actual=exc_info.value.status_code,
                  note="zpod is invisible to the permission-filtered lookup, not just forbidden")
        assert exc_info.value.status_code == 404
    """

    def _check(method: str, path: str, description: str, expected, actual, note: str = "") -> None:
        recorder.log_api(
            method, path, description, str(expected), str(actual),
            as_expected=(str(expected) == str(actual)), note=note, nodeid=request.node.nodeid,
        )

    return _check


# --------------------------------------------------------------------------
# Console: auto-banner from each test's docstring, diagnostics-on-failure,
# rich summary table at session end.
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _auto_banner(request):
    doc = (getattr(request.node, "function", None) and request.node.function.__doc__ or "").strip()
    if doc:
        banner(request.node.name, doc)
    module_name = request.node.module.__name__.rsplit(".", 1)[-1] if request.node.module else "misc"
    # Optional per-test narrative for the HTML report - see e2e.insight. A
    # test module may define a module-level INSIGHTS dict keyed by the
    # plain function name (request.function.__name__, not request.node.name,
    # so this still resolves correctly for parametrized tests).
    insights = getattr(request.node.module, "INSIGHTS", {}) if request.node.module else {}
    insight = insights.get(request.function.__name__)
    recorder.start_test(request.node.nodeid, request.node.name, doc, module_name, insight=insight)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a real diagnostic to the report for every failure, not just
    ones that called `diag.set_hint(...)` - critically, fixture *setup*
    failures (e.g. a shared fixture's raw SDK call hitting a 409) never run
    the test body, so there's no CLI call/api_check to show and no chance
    for the test to set a hint either - without this, those show up in the
    HTML report as a bare "failed" badge with zero explanation. Surfacing
    the actual exception (and which phase it happened in) here makes every
    failure self-explanatory from the report alone.
    """
    outcome = yield
    rep = outcome.get_result()
    hint = item.stash.get(diag_hint_key, None)
    if rep.when == "call" and rep.failed:
        if hint:
            rep.sections.append(("e2e diagnostics", hint))
            rep.e2e_diag_hint = hint

    if rep.when == "call" or (rep.when == "setup" and rep.outcome in ("skipped", "failed")):
        detail = hint or ""
        if rep.failed and call.excinfo is not None:
            where = "fixture setup (before the test body ran)" if rep.when == "setup" else "test body"
            exc_text = f"Failed during {where}: {call.excinfo.typename}: {call.excinfo.value}"
            detail = f"{detail}\n\n{exc_text}" if detail else exc_text
        recorder.finish_test(item.nodeid, rep.outcome, getattr(rep, "duration", 0.0), detail)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    from e2e.console import result_table

    results = []
    for outcome in ("passed", "failed", "skipped"):
        for rep in terminalreporter.stats.get(outcome, []):
            expected_when = "setup" if outcome == "skipped" else "call"
            if rep.when != expected_when:
                continue
            results.append(
                {
                    "name": rep.nodeid,
                    "outcome": outcome,
                    "duration": getattr(rep, "duration", 0.0),
                    "detail": getattr(rep, "e2e_diag_hint", ""),
                }
            )
    if results:
        result_table(results)
