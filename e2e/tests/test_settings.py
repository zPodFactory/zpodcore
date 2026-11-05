"""Settings CRUD + settings-driven deployment behavior.

`zcli setting` has no `get` subcommand - only `list` supports `--json`, so
tests filter the list output by name rather than fetching a single setting.
"""

import re
import time
from contextlib import contextmanager

import pytest

from e2e import cli
from e2e.config import ConfigError, load_settings
from e2e.insight import Beat, Insight
from e2e.naming import E2E_EMAIL_DOMAIN

BROADCOM_TOKEN_SETTING = "zpodfactory_broadcom_download_token"
OVA_STAGING_SETTING = "ff_endpoint_ova_staging"
REUSE_PASSWORD_SETTING = "ff_reuse_zpod_password"
DATASTORE_FLOOR_SETTING = "zpodfactory_datastore_min_free_pct"
ZCORE_PROFILE_PARAM = "zcore"  # the suite's own zcore-only profile, always compared
DEFAULT_PROFILE_SETTING = "ff_zpod_default_profile"
MAX_ZPODS_GLOBAL_SETTING = "ff_max_zpods_per_user"

# Narrative metadata for the HTML report, keyed by test function name - see
# e2e.insight. Purely decorative: never read by the tests below, only
# pulled by report.py at render time.
INSIGHTS = {
    "test_zpod_default_profile_used_when_profile_omitted": Insight(
        why="Typing --profile on every single `zpod create` is friction a lab operator shouldn't "
            "have to pay for their default, everyday case.",
        reasoning="ff_zpod_default_profile is read entirely client-side (zpodcli/cmd/zpod_cli.py) - "
                  "it's never sent to the API at all, so this only proves anything real if the CLI "
                  "itself is confirmed to fill it in before the request goes out, not just that the "
                  "setting exists in the database.",
        expected="`zcli zpod create` with no --profile flag still succeeds and reaches ACTIVE, and "
                 "the CLI announces which profile it silently picked.",
        beats=[
            Beat("ff_zpod_default_profile", "set to a real profile name", state="", color="info", tag="SETUP"),
            Beat("zpod create, no --profile", "CLI fills it in before calling the API", state="0", color="pass"),
            Beat("deploy", "reaches ACTIVE using the default", state="ACTIVE", color="pass"),
        ],
    ),
    "test_zpod_default_profile_missing_requires_explicit_profile": Insight(
        why="Silently defaulting to something arbitrary when nothing is configured would be far "
            "more confusing than a clear, immediate error.",
        reasoning="The fallback logic lives entirely in zcli, not the API - with no setting "
                  "configured, the CLI exits via typer.Exit(1) before ever calling zpods_create, so "
                  "this proves the failure happens at the right layer, with zero wasted API/deploy work.",
        expected="`zpod create` with no --profile and no default configured fails in the CLI itself "
                 "with a clear message, exit 1, no API call made.",
        beats=[
            Beat("ff_zpod_default_profile", "confirmed absent", state="", color="info", tag="SETUP"),
            Beat("zpod create, no --profile", "CLI's own fallback check", state="exit 1", color="pass", tag="FAILS BEFORE THE API"),
        ],
    ),
    "test_max_zpods_global_limit_enforced": Insight(
        why="A quota that only exists in documentation isn't a quota - the API itself has to "
            "actually say no.",
        reasoning="ZpodService.create() counts zpods where this identity has OWNER permission and "
                  "status != DELETED, then compares against ff_max_zpods_per_user before the new "
                  "zpod row is ever inserted - a cap of 1 keeps the test to exactly one real deploy "
                  "plus one instantly-rejected attempt, not a wall of setup.",
        expected="zPod #1 succeeds (right at the cap). zPod #2 is rejected with 406 and a detail "
                 "message naming the user and the limit - no zpod row created, no deploy work started.",
        beats=[
            Beat("ff_max_zpods_per_user = 1", "very low, on purpose", state="", color="info", tag="SETUP"),
            Beat("zpod create #1", "at the cap", state="ACTIVE", color="pass"),
            Beat("zpod create #2", "one over the cap", state="406", color="fail", tag="THE LIMIT"),
        ],
    ),
    "test_max_zpods_per_user_override_replaces_global": Insight(
        why="'Override' has to mean replace, not 'whichever number is stricter' - the two settings "
            "shouldn't interact at all once a per-user value exists.",
        reasoning="A looser global (3) paired with a stricter per-user override (1) isolates the "
                  "claim precisely: if the global were still contributing anything, a user who "
                  "already owns 1 zpod under global=3 would be allowed a 2nd. The service code only "
                  "ever consults the global value when no per-user row exists at all - it's a "
                  "fallback, not a blend.",
        expected="The per-user setting ff_max_zpods_<username> fully replaces "
                 "ff_max_zpods_per_user for that user - the rejection cites the override's limit "
                 "(1), not the global's (3).",
        beats=[
            Beat("global = 3, per-user override = 1", "deliberately looser global", state="", color="info", tag="SETUP"),
            Beat("zpod create #1", "at the override's cap", state="ACTIVE", color="pass"),
            Beat("zpod create #2", "global would allow it, override doesn't", state="406", color="fail", tag="OVERRIDE WINS"),
        ],
    ),
    "test_max_zpods_per_user_override_zero_means_unlimited": Insight(
        why="0 has to mean 'unlimited for this user' consistently - the same sentinel value the "
            "global setting already uses for missing/non-numeric.",
        reasoning="_parse_positive_int() treats 0 (and any non-positive or non-numeric value) as "
                  "unlimited, and the per-user setting merely existing short-circuits the global "
                  "lookup entirely - so a restrictive global (1) has zero effect on a user whose "
                  "own override is 0, not just a looser effect.",
        expected="Two real deploys succeed for the same user despite a global cap of 1, because "
                 "their personal override (0) means unlimited.",
        beats=[
            Beat("global = 1, per-user override = 0", "restrictive global, 0 override", state="", color="info", tag="SETUP"),
            Beat("zpod create #1 and #2", "both succeed", state="ACTIVE", color="pass", tag="UNLIMITED FOR THIS USER"),
        ],
    ),
}


def _find_setting(settings_json: list[dict], name: str) -> dict | None:
    return next((s for s in settings_json if s["name"] == name), None)


@contextmanager
def preserved_setting(runner, name: str, *, absent: bool = False):
    """Put setting `name` back exactly as it was (value and description, or absent) on exit.

    With absent=True the setting is removed for the duration. Every test that
    changes a real setting of the stack goes through this: the suite runs
    against live stacks, and a setting it leaves changed or deleted silently
    changes how that stack deploys.
    """
    original = _find_setting(runner.run_json("setting", "list").json, name)
    if original and set(original["value"]) == {"*"}:
        pytest.fail(f"setting {name} is masked in the API - its value can't be saved and restored")
    if absent and original:
        runner("setting", "delete", name)
    try:
        yield original
    finally:
        current = _find_setting(runner.run_json("setting", "list").json, name)
        if original is None:
            if current is not None:
                runner("setting", "delete", name, check=False)
        elif current is None:
            runner("setting", "create", "--name", name, "--value", original["value"],
                   "--description", original.get("description") or "", check=False)
        elif (current["value"], current.get("description")) != (original["value"], original.get("description")):
            runner("setting", "update", name, "--value", original["value"],
                   "--description", original.get("description") or "", check=False)
        restored = _find_setting(runner.run_json("setting", "list").json, name)
        restored_value = restored["value"] if restored else None
        original_value = original["value"] if original else None
        assert restored_value == original_value, (
            f"setting {name} not restored: was {original_value!r}, now {restored_value!r}"
        )


def test_setting_crud_roundtrip(zcli_as, namer):
    """Create, list, update, delete a setting through zcli; the value round-trips exactly."""
    runner = zcli_as("superadmin")
    name = namer("setting")

    result = runner("setting", "create", "--name", name, "--value", "hello", "--description", "e2e test setting")
    assert result.returncode == 0, f"setting create failed:\n{result.stderr}"

    listed = runner.run_json("setting", "list").json
    match = _find_setting(listed, name)
    assert match is not None, f"setting {name} not found after create"
    assert match["value"] == "hello", f"expected value 'hello', got {match['value']!r}"

    result = runner("setting", "update", name, "--value", "world")
    assert result.returncode == 0, f"setting update failed:\n{result.stderr}"
    listed = runner.run_json("setting", "list").json
    match = _find_setting(listed, name)
    assert match["value"] == "world", f"expected value 'world' after update, got {match['value']!r}"

    result = runner("setting", "delete", name)
    assert result.returncode == 0, f"setting delete failed:\n{result.stderr}"
    listed = runner.run_json("setting", "list").json
    assert _find_setting(listed, name) is None, f"setting {name} still present after delete"


def test_setting_duplicate_name_conflict(zcli_as, namer):
    """Creating a setting with a name that already exists fails cleanly (no crash, no silent overwrite)."""
    runner = zcli_as("superadmin")
    name = namer("setting-dup")
    runner("setting", "create", "--name", name, "--value", "1", "--description", "first")

    result = runner("setting", "create", "--name", name, "--value", "2", "--description", "second", check=False)
    assert result.returncode != 0, "creating a duplicate setting name should fail"

    runner("setting", "delete", name, check=False)


def test_setting_delete_missing_fails_cleanly(zcli_as, namer):
    """Deleting a setting that doesn't exist fails cleanly rather than crashing."""
    runner = zcli_as("superadmin")
    result = runner("setting", "delete", namer("setting-missing"), check=False)
    assert result.returncode != 0, "deleting a nonexistent setting should fail"


def test_broadcom_token_value_is_masked_when_set(zcli_as):
    """zpodfactory_broadcom_download_token is masked as '********' in API responses when non-empty - never assert on the real value."""
    runner = zcli_as("superadmin")
    listed = runner.run_json("setting", "list").json
    match = _find_setting(listed, BROADCOM_TOKEN_SETTING)
    assert match is not None, f"expected seeded setting {BROADCOM_TOKEN_SETTING} to exist"
    if match["value"]:
        assert match["value"] == "********", (
            f"expected masked value for {BROADCOM_TOKEN_SETTING}, got a raw-looking value"
        )


def test_settings_read_allowed_mutation_denied_for_non_superadmin(zcli_as, namer):
    """A non-superadmin can read settings (GET /settings has no superadmin gate -
    only create/update/delete do, see zpodapi/settings/setting__routes.py), but
    can't create/modify/delete one.

    Originally assumed (from stale docs) that listing itself was blocked;
    confirmed against route source this is intentional - only the mutating
    routes carry `dependencies=[GlobalDepends.OnlySuperAdmin]`.
    """
    runner = zcli_as("test_user")

    result = runner("setting", "list", "--json", "--no-color")
    assert result.returncode == 0, f"expected non-superadmin to be able to list settings:\n{result.stderr}"
    assert isinstance(result.json, list), "expected a JSON list of settings"

    result = runner(
        "setting", "create", "--name", namer("setting-denied"), "--value", "x", "--description", "x", check=False
    )
    assert result.returncode != 0, "non-superadmin should not be able to create a setting"


@pytest.fixture
def ova_staging_setting(zcli_as):
    """Snapshots ff_endpoint_ova_staging and restores it in teardown regardless of test outcome."""
    runner = zcli_as("superadmin")
    with preserved_setting(runner, OVA_STAGING_SETTING):
        yield runner


def pytest_generate_tests(metafunc):
    """The staging test runs once per profile: the suite's own zcore-only profile,
    then each profile named in E2E_OVA_STAGING_PROFILES."""
    if "staging_profile" in metafunc.fixturenames:
        try:
            extra = load_settings().ova_staging_profile_list
        except ConfigError:
            extra = []
        profiles = [ZCORE_PROFILE_PARAM, *[p for p in extra if p != ZCORE_PROFILE_PARAM]]
        metafunc.parametrize("staging_profile", profiles, ids=profiles)


def _fmt_seconds(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = round(seconds)
    return f"{seconds // 60}m{seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


def _gain(off: float | None, on: float | None) -> str:
    if not off or on is None:
        return "-"
    pct = (on - off) / off * 100
    return f"{pct:+.0f}% ({off / on:.1f}x)" if on else f"{pct:+.0f}%"


@pytest.mark.destructive
@pytest.mark.slow
def test_ff_endpoint_ova_staging_toggle_both_deploy(
    staging_profile, ova_staging_setting, request, endpoint, namer, superadmin_client, e2e_config,
    prefect_diag, poll_zpod_deleted,
):
    """A profile deploys with ff_endpoint_ova_staging off and on; the report shows the deploy time of each.

    ff_endpoint_ova_staging changes whether L1 OVAs are uploaded on every
    deploy, or staged once as templates and cloned per deploy. Both paths
    must reach an ACTIVE zPod. The report gets one table per profile: the
    zcli wait time, the Prefect flow time and each component's deploy task,
    off vs on, so the gain is visible component by component. Times are
    shown, never asserted: they depend on the endpoint's load. The staging-on
    deploy reuses templates already staged, so it shows the warm path.

    Each deploy is destroyed (and waited for) before the next one starts:
    only one test zPod of the profile exists at a time. The setting is
    always restored to its original value.
    """
    from e2e.report import recorder

    runner = ova_staging_setting
    if staging_profile == ZCORE_PROFILE_PARAM:
        profile = request.getfixturevalue("zcore_profile")
    else:
        profile = staging_profile
        if not any(p.name == profile for p in superadmin_client.profiles_get_all.sync() or []):
            pytest.fail(f"profile {profile} (E2E_OVA_STAGING_PROFILES) doesn't exist on the server")
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    timings: dict[str, dict] = {}
    for value in ("false", "true"):
        runner("setting", "update", OVA_STAGING_SETTING, "--value", value)

        short = re.sub(r"[^a-z0-9]+", "-", staging_profile.lower()).strip("-")[:10]
        zpod_name = namer(f"ova-{short}-{'on' if value == 'true' else 'off'}")
        start = time.monotonic()
        result = runner(
            "zpod", "create", zpod_name,
            "--endpoint", endpoint.name,
            "--profile", profile,
            "--wait", "--no-spinner",
            check=False,
            timeout=deploy_timeout,
        )
        wall = time.monotonic() - start
        assert result.returncode == 0, (
            f"{profile} deploy with {OVA_STAGING_SETTING}={value} failed:\n{result.stdout}\n{result.stderr}"
        )
        zpod = superadmin_client.zpods_get.sync(id=f"name={zpod_name}")
        assert zpod.status == "ACTIVE", f"zpod {zpod_name} not ACTIVE ({OVA_STAGING_SETTING}={value}): {zpod.status}"
        timings[value] = {"wall": wall, **prefect_diag.deploy_timings(zpod_name)}

        runner("zpod", "destroy", zpod_name)
        poll_zpod_deleted(superadmin_client, f"name={zpod_name}")

    off, on = timings["false"], timings["true"]
    components = list(dict.fromkeys([*off.get("components", {}), *on.get("components", {})]))
    rows = [
        [c, _fmt_seconds(off.get("components", {}).get(c)), _fmt_seconds(on.get("components", {}).get(c)),
         _gain(off.get("components", {}).get(c), on.get("components", {}).get(c))]
        for c in sorted(components)
    ]
    rows.append(["Total, Prefect deploy flow", _fmt_seconds(off.get("flow")), _fmt_seconds(on.get("flow")),
                 _gain(off.get("flow"), on.get("flow"))])
    rows.append(["Total, zcli create --wait", _fmt_seconds(off["wall"]), _fmt_seconds(on["wall"]),
                 _gain(off["wall"], on["wall"])])
    recorder.log_table(
        f"profile {profile}: deploy time, OVA staging off vs on",
        ["component (deploy task)", "staging off", "staging on", "change"],
        rows,
        summary=f"{profile}: {_fmt_seconds(off['wall'])} → {_fmt_seconds(on['wall'])} "
                f"with OVA staging ({_gain(off['wall'], on['wall'])})",
    )


@pytest.fixture
def default_profile_setting(zcli_as):
    """ff_zpod_default_profile is absent during the test and put back as it was afterwards.

    It's read by every `zcli zpod create` that omits --profile, so the test
    needs a known state - and the stack's own value must come back.
    """
    runner = zcli_as("superadmin")
    with preserved_setting(runner, DEFAULT_PROFILE_SETTING, absent=True):
        yield runner


@pytest.fixture
def max_zpods_per_user_setting(zcli_as):
    """ff_max_zpods_per_user is absent during the test and put back as it was afterwards.

    A global cap affects every non-superadmin zpod creation, so the test
    starts from no cap - and the stack's own cap must come back.
    """
    runner = zcli_as("superadmin")
    with preserved_setting(runner, MAX_ZPODS_GLOBAL_SETTING, absent=True):
        yield runner


@pytest.fixture
def limited_owner(superadmin_client, zcli_as, namer, endpoint, e2e_config, keep_resources):
    """A throwaway non-superadmin identity, granted permission on `endpoint`,
    with a guaranteed-zero owned-zpod count.

    The ff_max_zpods_* tests need to know *exactly* how many zpods this
    identity owns going in - the shared session-scoped test_owner/test_user
    identities can't guarantee that (other tests may have deployed under
    them and not torn down yet), so this provisions a fresh one instead, the
    same way conftest.py's own `_role_identities` does.
    """
    from zpodsdk.models.user_create import UserCreate

    from e2e.client_factory import build_client

    username = namer("user-maxzpods")
    user = superadmin_client.users_create.sync(
        body=UserCreate(
            username=username, email=f"{username}@{E2E_EMAIL_DOMAIN}",
            description="e2e ff_max_zpods test identity",
        )
    )
    client = build_client(e2e_config.api_base_url, user.api_token)
    factory_name = namer("factory-maxzpods")
    cli.add_factory(factory_name, e2e_config.api_base_url, user.api_token)

    superadmin_runner = zcli_as("superadmin")
    superadmin_runner("endpoint", "permission", "add", endpoint.name, "--username", username)

    yield cli.RoleRunner(factory=factory_name), client, username

    if not keep_resources:
        superadmin_runner("endpoint", "permission", "remove", endpoint.name, "--username", username, check=False)
        cli.remove_factory(factory_name)
        try:
            superadmin_client.users_delete.sync(id=f"username={username}")
        except Exception:
            pass


@pytest.mark.destructive
@pytest.mark.slow
def test_zpod_default_profile_used_when_profile_omitted(
    default_profile_setting, zcore_profile, endpoint, namer, superadmin_client, e2e_config, poll_zpod_deleted,
):
    """Setting ff_zpod_default_profile lets `zcli zpod create` succeed with no --profile flag at all."""
    runner = default_profile_setting
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    result = runner(
        "setting", "create", "--name", DEFAULT_PROFILE_SETTING, "--value", zcore_profile,
        "--description", "e2e default profile test",
    )
    assert result.returncode == 0, f"setting create failed:\n{result.stderr}"

    zpod_name = namer("default-profile")
    result = runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"zpod create with no --profile (default set) failed:\n{result.stdout}\n{result.stderr}"
    assert "using default profile" in result.stdout.lower(), (
        f"expected the CLI to announce it used the default profile, got:\n{result.stdout}"
    )

    zpod = superadmin_client.zpods_get.sync(id=f"name={zpod_name}")
    assert zpod.status == "ACTIVE", f"expected ACTIVE, got {zpod.status}"

    runner("zpod", "destroy", zpod_name)
    poll_zpod_deleted(superadmin_client, f"name={zpod_name}")


@pytest.mark.destructive
def test_zpod_default_profile_missing_requires_explicit_profile(default_profile_setting, namer, endpoint):
    """Without ff_zpod_default_profile set, omitting --profile fails in the CLI itself - no API call is ever made."""
    runner = default_profile_setting
    result = runner("zpod", "create", namer("no-default-profile"), "--endpoint", endpoint.name, check=False)
    assert result.returncode != 0, "zpod create with no --profile and no default setting should fail"
    assert "no profile specified" in result.stdout.lower(), (
        f"expected the CLI's own 'no profile specified' error, got:\n{result.stdout}"
    )


@pytest.mark.destructive
@pytest.mark.slow
def test_max_zpods_global_limit_enforced(
    max_zpods_per_user_setting, limited_owner, zcore_profile, endpoint, namer,
    superadmin_client, e2e_config, api_check, poll_zpod_deleted,
):
    """A non-superadmin at ff_max_zpods_per_user is rejected by the API itself on the next create - the server, not the CLI."""
    from zpodsdk.errors import UnexpectedStatus
    from zpodsdk.models.zpod_create import ZpodCreate

    admin_runner = max_zpods_per_user_setting
    owner_runner, owner_client, owner_username = limited_owner
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60

    admin_runner(
        "setting", "create", "--name", MAX_ZPODS_GLOBAL_SETTING, "--value", "1",
        "--description", "e2e ff_max_zpods_per_user test",
    )

    zpod_name = namer("maxzpods-cap1")
    result = owner_runner(
        "zpod", "create", zpod_name,
        "--endpoint", endpoint.name,
        "--profile", zcore_profile,
        "--wait", "--no-spinner",
        check=False,
        timeout=deploy_timeout,
    )
    assert result.returncode == 0, f"first zpod (at the cap of 1) should succeed:\n{result.stdout}\n{result.stderr}"

    with pytest.raises(UnexpectedStatus) as exc_info:
        owner_client.zpods_create.sync(
            body=ZpodCreate(name=namer("maxzpods-cap1-over"), endpoint_id=endpoint.id, profile=zcore_profile)
        )
    detail = exc_info.value.content.decode(errors="ignore")
    api_check(
        "POST", "/zpods", f"{owner_username} already owns 1 zpod, {MAX_ZPODS_GLOBAL_SETTING}=1",
        expected=406, actual=exc_info.value.status_code, note=detail.strip(),
    )
    assert exc_info.value.status_code == 406, f"expected 406 over the cap, got {exc_info.value.status_code}: {detail}"
    assert owner_username in detail, f"expected the username in the rejection detail, got: {detail}"

    owner_runner("zpod", "destroy", zpod_name, check=False)
    try:
        poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
    except Exception:
        pass


@pytest.mark.destructive
@pytest.mark.slow
def test_max_zpods_per_user_override_replaces_global(
    max_zpods_per_user_setting, limited_owner, zcore_profile, endpoint, namer,
    superadmin_client, e2e_config, api_check, poll_zpod_deleted,
):
    """A per-user ff_max_zpods_<username> override fully replaces the global value for that user -
    a *stricter* override still wins over a looser global, proving it's a replacement, not a blend."""
    from zpodsdk.errors import UnexpectedStatus
    from zpodsdk.models.zpod_create import ZpodCreate

    admin_runner = max_zpods_per_user_setting
    owner_runner, owner_client, owner_username = limited_owner
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60
    user_setting_name = f"ff_max_zpods_{owner_username}"

    admin_runner(
        "setting", "create", "--name", MAX_ZPODS_GLOBAL_SETTING, "--value", "3",
        "--description", "e2e override test - global",
    )
    admin_runner(
        "setting", "create", "--name", user_setting_name, "--value", "1",
        "--description", "e2e override test - per-user",
    )

    try:
        zpod_name = namer("maxzpods-override1")
        result = owner_runner(
            "zpod", "create", zpod_name,
            "--endpoint", endpoint.name,
            "--profile", zcore_profile,
            "--wait", "--no-spinner",
            check=False,
            timeout=deploy_timeout,
        )
        assert result.returncode == 0, f"first zpod (at the override's cap of 1) should succeed:\n{result.stdout}\n{result.stderr}"

        with pytest.raises(UnexpectedStatus) as exc_info:
            owner_client.zpods_create.sync(
                body=ZpodCreate(name=namer("maxzpods-override1-over"), endpoint_id=endpoint.id, profile=zcore_profile)
            )
        detail = exc_info.value.content.decode(errors="ignore")
        api_check(
            "POST", "/zpods", f"{owner_username}: global=3 but per-user override=1 - the override should win",
            expected=406, actual=exc_info.value.status_code, note=detail.strip(),
        )
        assert exc_info.value.status_code == 406, (
            f"expected the stricter per-user override (1) to win over the looser global (3), "
            f"got {exc_info.value.status_code}: {detail}"
        )
        assert "(1)" in detail, f"expected the rejection to cite the per-user limit (1), not the global (3): {detail}"

        owner_runner("zpod", "destroy", zpod_name, check=False)
        try:
            poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
        except Exception:
            pass
    finally:
        admin_runner("setting", "delete", user_setting_name, check=False)


@pytest.mark.destructive
@pytest.mark.slow
def test_max_zpods_per_user_override_zero_means_unlimited(
    max_zpods_per_user_setting, limited_owner, zcore_profile, endpoint, namer,
    superadmin_client, e2e_config, poll_zpod_deleted,
):
    """A per-user override of 0 means unlimited for that user specifically, even under a
    restrictive global cap - proves the override is a full replacement, not just a tighter number."""
    admin_runner = max_zpods_per_user_setting
    owner_runner, owner_client, owner_username = limited_owner
    deploy_timeout = e2e_config.deploy_timeout_seconds + 60
    user_setting_name = f"ff_max_zpods_{owner_username}"

    admin_runner(
        "setting", "create", "--name", MAX_ZPODS_GLOBAL_SETTING, "--value", "1",
        "--description", "e2e override test - restrictive global",
    )
    admin_runner(
        "setting", "create", "--name", user_setting_name, "--value", "0",
        "--description", "e2e override test - 0 means unlimited",
    )

    created = []
    try:
        for i in range(2):  # more than the global cap of 1 - both must succeed
            zpod_name = namer(f"maxzpods-unlimited-{i}")
            result = owner_runner(
                "zpod", "create", zpod_name,
                "--endpoint", endpoint.name,
                "--profile", zcore_profile,
                "--wait", "--no-spinner",
                check=False,
                timeout=deploy_timeout,
            )
            assert result.returncode == 0, (
                f"zpod #{i + 1} should succeed - per-user override of 0 means unlimited despite global=1:\n"
                f"{result.stdout}\n{result.stderr}"
            )
            created.append(zpod_name)
    finally:
        for zpod_name in created:
            owner_runner("zpod", "destroy", zpod_name, check=False)
        for zpod_name in created:
            try:
                poll_zpod_deleted(superadmin_client, f"name={zpod_name}")
            except Exception:
                pass
        admin_runner("setting", "delete", user_setting_name, check=False)


def _set_setting(runner, name: str, value: str) -> None:
    if _find_setting(runner.run_json("setting", "list").json, name):
        runner("setting", "update", name, "--value", value)
    else:
        runner("setting", "create", "--name", name, "--value", value, "--description", "e2e")


def _deploy(runner, name, endpoint, profile, e2e_config, superadmin_client):
    result = runner("zpod", "create", name, "--endpoint", endpoint.name, "--profile", profile,
                    "--wait", "--no-spinner", check=False, timeout=e2e_config.deploy_timeout_seconds + 60)
    zpod = superadmin_client.zpods_get.sync(id=f"name={name}")
    assert result.returncode == 0 and zpod.status == "ACTIVE", f"{name}: {zpod.status}\n{result.stdout}"
    return zpod


def _destroy(runner, name, superadmin_client, poll_zpod_deleted):
    runner("zpod", "destroy", name, check=False)
    poll_zpod_deleted(superadmin_client, f"name={name}")


@pytest.mark.destructive
@pytest.mark.slow
def test_reuse_zpod_password_on_redeploy(
    zcli_as, zcore_profile, endpoint, namer, superadmin_client, e2e_config, poll_zpod_deleted,
):
    """With ff_reuse_zpod_password=true a zPod redeployed under the same name gets its old password; with false, a new one."""
    runner = zcli_as("superadmin")
    name = namer("pwreuse")
    with preserved_setting(runner, REUSE_PASSWORD_SETTING):
        _set_setting(runner, REUSE_PASSWORD_SETTING, "true")
        try:
            first = _deploy(runner, name, endpoint, zcore_profile, e2e_config, superadmin_client).password
            _destroy(runner, name, superadmin_client, poll_zpod_deleted)
            again = _deploy(runner, name, endpoint, zcore_profile, e2e_config, superadmin_client).password
            assert again == first, "ff_reuse_zpod_password=true: redeploy got a new password"
            _destroy(runner, name, superadmin_client, poll_zpod_deleted)

            _set_setting(runner, REUSE_PASSWORD_SETTING, "false")
            fresh = _deploy(runner, name, endpoint, zcore_profile, e2e_config, superadmin_client).password
            assert fresh != first, "ff_reuse_zpod_password=false: redeploy kept the old password"
        finally:
            _destroy(runner, name, superadmin_client, poll_zpod_deleted)


@pytest.mark.destructive
@pytest.mark.slow
def test_datastore_floor_refuses_disk_add_and_deploy(
    zcli_as, zcore_zpod, zcore_profile, endpoint, namer, superadmin_client, e2e_config, poll_zpod_deleted,
):
    """With zpodfactory_datastore_min_free_pct above the datastore's free space, a disk add and a zPod deploy both fail before creating anything.

    The floor is hard for everyone: while it is raised, any deploy on the
    endpoint fails. It is up for about a minute and always restored.
    """
    runner = zcli_as("superadmin")
    name = namer("floor")
    disks_before = {d["device"] for d in runner.run_json("zpod", "disk", "list", zcore_zpod).json}
    with preserved_setting(runner, DATASTORE_FLOOR_SETTING):
        _set_setting(runner, DATASTORE_FLOOR_SETTING, "99")
        try:
            result = runner("zpod", "disk", "add", zcore_zpod, "--size", "1", check=False, timeout=900)
            output = result.stdout + result.stderr
            assert result.returncode != 0, f"disk add under the floor did not fail:\n{output}"
            assert "floor" in output.lower() or DATASTORE_FLOOR_SETTING in output, f"no floor reason:\n{output}"
            disks_after = {d["device"] for d in runner.run_json("zpod", "disk", "list", zcore_zpod).json}
            assert disks_after == disks_before, f"a disk was added under the floor: {disks_after - disks_before}"

            result = runner("zpod", "create", name, "--endpoint", endpoint.name, "--profile", zcore_profile,
                            "--wait", "--no-spinner", check=False, timeout=e2e_config.deploy_timeout_seconds + 60)
            zpod = superadmin_client.zpods_get.sync(id=f"name={name}")
            assert zpod.status == "DEPLOY_FAILED", f"deploy under the floor: {zpod.status}\n{result.stdout}"
            components = superadmin_client.zpods_components_get_all.sync(id=f"name={name}") or []
            assert not [c for c in components if c.status == "ACTIVE"], "a component was deployed under the floor"
        finally:
            _destroy(runner, name, superadmin_client, poll_zpod_deleted)
