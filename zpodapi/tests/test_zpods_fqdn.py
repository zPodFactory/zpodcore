"""FQDN length guardrail on POST /zpods and POST /zpods/{id}/components.

Linux caps the system hostname at 64 chars even for a full FQDN. The API
rejects, up front, any zPod/component combination whose resulting FQDN would
exceed 64 minus the `zpodfactory_fqdn_reserved_chars` margin (default 8 → 56).
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from zpodcommon import models as M
from zpodcommon.lib.dbutils import DBUtils

SHORT_DOMAIN = "veryyyyyylong.subdomain.domain.com"  # 34 chars
LONG_DOMAIN = "verylongcorporate.subdomain.example.com"  # 39 chars


class FakeZpodEngineClient:
    """Stand-in for the Prefect client so no flow run is scheduled."""

    calls: list[dict] = []

    def create_flow_run_by_name(self, flow_name, deployment_name=None, **kw):
        self.calls.append({"flow_name": flow_name, **kw})


@pytest.fixture(autouse=True)
def settings_and_engine(monkeypatch):
    """Serve settings from a dict and stub out the engine / zbox calls."""
    values = {"zpodfactory_default_domain": SHORT_DOMAIN}
    monkeypatch.setattr(
        DBUtils,
        "get_setting_value",
        classmethod(lambda cls, name: values.get(name)),
    )
    FakeZpodEngineClient.calls = []
    monkeypatch.setattr(
        "zpodapi.zpods.zpod__services.ZpodEngineClient", FakeZpodEngineClient
    )
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_component__services.ZpodEngineClient",
        FakeZpodEngineClient,
    )
    monkeypatch.setattr(
        "zpodapi.zpods.zpod_component__services.get_all_active_addresses",
        lambda zpod: set(),
    )
    return values


@pytest.fixture
def catalog(session: Session):
    """One ACTIVE endpoint, the vcfinstaller component, and a profile using it."""
    endpoint = M.Endpoint(name="ep", endpoints={}, status="ACTIVE")
    components = [
        M.Component(
            component_uid=f"{name}-{version}",
            component_name=name,
            component_version=version,
            component_description=name,
            filename=f"{name}.ova",
            jsonfile=f"/library/{name}.json",
            status="ACTIVE",
            download_status="COMPLETED",
            file_checksum="abc",
        )
        for name, version in (("zcore", "1.0.0"), ("vcfinstaller", "9.0.0.0"))
    ]
    # zcore-* must be the first profile element; vcfinstaller is the longest name.
    profile = M.Profile(
        name="vcf910",
        profile=[
            {"component_uid": "zcore-1.0.0"},
            {"component_uid": "vcfinstaller-9.0.0.0"},
        ],
    )
    session.add_all([endpoint, *components, profile])
    session.commit()
    return endpoint


def _create_zpod(client: TestClient, name: str, **extra):
    return client.post(
        "/zpods",
        json={"name": name, "endpoint_id": 1, "profile": "vcf910", **extra},
    )


# --- POST /zpods -------------------------------------------------------------


def test_create_zpod_fqdn_within_limit(superadmin_client, catalog):
    # vcfinstaller.test.veryyyyyylong.subdomain.domain.com -> 52 chars <= 56
    response = _create_zpod(superadmin_client, "test")
    assert response.status_code == 201, response.text
    assert response.json()["name"] == "test"
    assert FakeZpodEngineClient.calls[0]["flow_name"] == "zpod_deploy"


def test_create_zpod_fqdn_too_long(superadmin_client, catalog, settings_and_engine):
    settings_and_engine["zpodfactory_default_domain"] = LONG_DOMAIN
    # vcfinstaller.training.verylongcorporate.subdomain.example.com -> 61 > 56
    response = _create_zpod(superadmin_client, "training")
    assert response.status_code == 400, response.text
    detail = response.json()["detail"]
    assert detail.startswith(
        "zPod FQDN naming is too long: "
        "'vcfinstaller.training.verylongcorporate.subdomain.example.com' "
        "is 61 characters, which exceeds the 56-character limit"
    )
    assert FakeZpodEngineClient.calls == []  # rejected before any flow run


def test_create_zpod_explicit_domain_too_long(superadmin_client, catalog):
    # A short zPod name still fails if --domain alone pushes it over.
    # vcfinstaller.a-very-long-explicit-domain-override.example.com -> 61 > 56
    response = _create_zpod(
        superadmin_client,
        "t",
        domain="a-very-long-explicit-domain-override.example.com",
    )
    assert response.status_code == 400, response.text
    assert (
        "is 61 characters, which exceeds the 56-character limit"
        in (response.json()["detail"])
    )


def test_create_zpod_boundary(superadmin_client, catalog, settings_and_engine):
    # Exactly 56 chars passes, 57 fails (off-by-one guard).
    # "vcfinstaller." (13) + "test." (5) + domain -> domain must be 38 chars.
    settings_and_engine["zpodfactory_default_domain"] = "x" * 38
    assert _create_zpod(superadmin_client, "test").status_code == 201
    settings_and_engine["zpodfactory_default_domain"] = "x" * 39
    assert _create_zpod(superadmin_client, "test2").status_code == 400


def test_create_zpod_reserved_chars_setting(
    superadmin_client, catalog, settings_and_engine
):
    # Lowering the margin to 0 makes the 61-char FQDN acceptable (<= 64).
    settings_and_engine["zpodfactory_default_domain"] = LONG_DOMAIN
    settings_and_engine["zpodfactory_fqdn_reserved_chars"] = "0"
    assert _create_zpod(superadmin_client, "training").status_code == 201


def test_create_zpod_profile_hostname_override_is_checked(
    superadmin_client, catalog, session
):
    # The profile's own "hostname" wins over component_name, as at deploy.
    profile = session.get(M.Profile, 1)
    profile.profile = [
        {"component_uid": "zcore-1.0.0"},
        {
            "component_uid": "vcfinstaller-9.0.0.0",
            "hostname": "a-much-longer-custom-hostname-than-usual",
        },
    ]
    session.add(profile)
    session.commit()
    response = _create_zpod(superadmin_client, "test")
    assert response.status_code == 400, response.text
    assert (
        "a-much-longer-custom-hostname-than-usual.test." in (response.json()["detail"])
    )


# --- POST /zpods/{id}/components ------------------------------------------


@pytest.fixture
def deployed_zpod(session: Session, catalog):
    """A zPod as the deploy prep flow leaves it: domain set, one network."""
    zpod = M.Zpod(
        name="training",
        domain=f"training.{LONG_DOMAIN}",
        endpoint_id=catalog.id,
        profile="vcf910",
        status="ACTIVE",
        networks=[M.ZpodNetwork(cidr="10.96.1.0/24")],
    )
    session.add(zpod)
    session.commit()
    return zpod


def test_component_add_fqdn_too_long(superadmin_client, deployed_zpod):
    # vcfinstaller.training.verylongcorporate.subdomain.example.com -> 61 > 56
    response = superadmin_client.post(
        f"/zpods/{deployed_zpod.id}/components",
        json={"component_uid": "vcfinstaller-9.0.0.0"},
    )
    assert response.status_code == 400, response.text
    assert (
        "is 61 characters, which exceeds the 56-character limit"
        in (response.json()["detail"])
    )
    assert FakeZpodEngineClient.calls == []


def test_component_add_fqdn_within_limit(superadmin_client, deployed_zpod, session):
    deployed_zpod.domain = f"test.{SHORT_DOMAIN}"
    session.add(deployed_zpod)
    session.commit()
    response = superadmin_client.post(
        f"/zpods/{deployed_zpod.id}/components",
        json={"component_uid": "vcfinstaller-9.0.0.0"},
    )
    assert response.status_code == 201, response.text
    assert FakeZpodEngineClient.calls[0]["flow_name"] == "zpod_component_add"
