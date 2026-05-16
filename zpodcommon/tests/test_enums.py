"""Smoke tests for zpodcommon enums.

zpodcommon has no venv of its own; these tests run via zpodengine's venv
(see zpodengine/pyproject.toml [tool.pytest.ini_options] testpaths).
"""

from zpodcommon.enums import (
    ComponentStatus,
    EndpointComputeDrivers,
    EndpointStatus,
    UserStatus,
    ZpodStatus,
)


def test_case_insensitive_lookup():
    # EndpointComputeDrivers inherits (str, CaseInsensitiveEnum); look-up works regardless of case.
    assert EndpointComputeDrivers("vsphere") == EndpointComputeDrivers.VSPHERE
    assert EndpointComputeDrivers("VSPHERE") == EndpointComputeDrivers.VSPHERE
    assert EndpointComputeDrivers("VSphere") == EndpointComputeDrivers.VSPHERE


def test_component_status_values():
    assert ComponentStatus.ACTIVE.value == "ACTIVE"


def test_endpoint_status_values():
    assert EndpointStatus.ACTIVE.value == "ACTIVE"


def test_user_status_values():
    assert UserStatus.ENABLED.value == "ENABLED"
    assert UserStatus.DISABLED.value == "DISABLED"


def test_zpod_status_has_expected_states():
    values = {s.value for s in ZpodStatus}
    assert "ACTIVE" in values
