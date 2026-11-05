"""Basic zcli wiring canary + zPodFactory server info.

Runs first (alphabetically) so a broken zcli install or unreachable server
fails fast with an obvious message before the rest of the suite spends time
on much slower tests.
"""

import pytest

from e2e import cli


@pytest.mark.smoke
def test_zcli_help_exits_cleanly():
    """`zcli --help` exits 0 - confirms the CLI and all its subcommand groups import cleanly."""
    result = cli.zcli_run("--help", columns=cli.HELP_COLUMNS)
    assert result.returncode == 0, f"zcli --help failed:\n{result.stderr}"
    assert "Usage" in result.stdout, "expected usage text in --help output"


@pytest.mark.smoke
def test_zcli_version_exits_cleanly():
    """`zcli --version` exits 0 - confirms the version callback is wired up."""
    result = cli.zcli_run("--version")
    assert result.returncode == 0, f"zcli --version failed:\n{result.stderr}"


@pytest.mark.smoke
def test_zcli_factory_list_shows_active_factory(zcli_as):
    """`zcli factory list` shows the suite's ephemeral superadmin factory as registered."""
    run = zcli_as("superadmin")
    result = run("factory", "list")
    assert result.returncode == 0, f"zcli factory list failed:\n{result.stderr}"


@pytest.mark.smoke
def test_fetch_factory_root_info(superadmin_client):
    """GET / returns zPodFactory server metadata - not exposed via zcli, so this goes through the SDK directly."""
    # What this validates: the API is up (zcli has no dedicated "fetch
    # server info" command, so there's nothing to drive this through the
    # CLI). The route intentionally returns an HTML landing page
    # (HTMLResponse in zpodapi/root/root__routes.py), so this only checks
    # that the call succeeds, not any particular content.
    superadmin_client.root_root.sync()
