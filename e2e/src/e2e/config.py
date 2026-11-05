"""Environment configuration for the e2e suite.

All configuration comes from a single `.env` file (see `.env.sample`) -
deliberately not from any pre-existing `zcli` factory config on the host,
so the suite stays portable across machines and never touches the
operator's own zcli setup.
"""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: str = Field(alias="E2E_API_BASE_URL")
    superadmin_token: str = Field(alias="E2E_SUPERADMIN_TOKEN")
    endpoint_name: str = Field(alias="E2E_ENDPOINT_NAME")

    download_source_dir: str = Field(
        default="~/downloads", alias="E2E_DOWNLOAD_SOURCE_DIR"
    )
    products_path: str = Field(default="/zPod/Products", alias="E2E_PRODUCTS_PATH")
    # Copy of the server's zpodfactory_broadcom_download_token. The API masks
    # it, so the no-token test can only blank it and put it back with this copy.
    broadcom_token: SecretStr = Field(default=SecretStr(""), alias="E2E_BROADCOM_TOKEN")

    dns_resolver: str = Field(alias="E2E_DNS_RESOLVER")

    # --- On-host verification (SSH into the zPods the suite deploys) ---
    # Private key matching the server's zpodfactory_ssh_key setting. The
    # appliance generates ~/.ssh/id_rsa for root at first boot and stores
    # its public half in that setting, so the default works there.
    zpod_ssh_key: Path = Field(default=Path("~/.ssh/id_rsa"), alias="E2E_ZPOD_SSH_KEY")
    zcore_component_uid: str = Field(default="zcore-13.7", alias="E2E_ZCORE_COMPONENT_UID")
    zbox_component_uid: str = Field(default="zbox-13.7.1", alias="E2E_ZBOX_COMPONENT_UID")

    # --- zPod networks (VLANs on zcore) ---
    user_vlan: int = Field(default=111, alias="E2E_USER_VLAN")
    user_vlan_gateway: str = Field(default="10.42.111.1/24", alias="E2E_USER_VLAN_GATEWAY")
    second_vlan: int = Field(default=112, alias="E2E_SECOND_VLAN")
    second_vlan_gateway: str = Field(default="10.42.112.1/24", alias="E2E_SECOND_VLAN_GATEWAY")
    # A URL a VM behind zcore can only reach with masquerade on (or a route back).
    internet_probe_url: str = Field(default="https://github.com", alias="E2E_INTERNET_PROBE_URL")
    # Global routing really advertises a subnet into the NSX fabric. Off by
    # default: the suite then only runs `routing --dry-run` (fabric checks,
    # nothing changed). Turn on for a lab whose fabric accepts the subnet.
    fabric_routing: bool = Field(default=False, alias="E2E_FABRIC_ROUTING")
    # The network the fabric test adds as global. Empty gateway: 192.168.<x>.1/24,
    # x = third octet of the test zPod's own range (unique per zPod).
    global_vlan: int = Field(default=113, alias="E2E_GLOBAL_VLAN")
    global_vlan_gateway: str = Field(default="", alias="E2E_GLOBAL_VLAN_GATEWAY")

    # --- Component placement / extraConfig (opt-in, heavier) ---
    # A profile (name on the server) whose zPods have a vCenter, for nested
    # component placement tests. Empty: those tests are skipped.
    nested_profile: str = Field(default="", alias="E2E_NESTED_PROFILE")
    # An extraConfig (guestinfo.*) image to deploy and log into, e.g. photon-5.0
    # or ubuntu-24.04. Empty: skipped.
    extraconfig_component_uid: str = Field(default="", alias="E2E_EXTRACONFIG_COMPONENT_UID")

    # --- OVA staging comparison ---
    # Extra profiles (names on the server, comma separated) the
    # ff_endpoint_ova_staging test deploys with staging off then on, next to
    # the suite's own zcore-only profile, to show the deploy time difference
    # per component. Each one costs two full deploys. Empty: zcore only.
    ova_staging_profiles: str = Field(default="", alias="E2E_OVA_STAGING_PROFILES")

    @field_validator("resource_prefix")
    @classmethod
    def _prefix_not_empty(cls, v: str) -> str:
        # The cleanup sweep deletes everything whose name starts with this:
        # an empty prefix would match every zPod, user and profile on the stack.
        if not v.strip():
            raise ValueError("E2E_RESOURCE_PREFIX must not be empty (e.g. e2e-)")
        return v

    @property
    def ova_staging_profile_list(self) -> list[str]:
        return [p.strip() for p in self.ova_staging_profiles.split(",") if p.strip()]

    resource_prefix: str = Field(default="e2e-", alias="E2E_RESOURCE_PREFIX")
    keep_resources: bool = Field(default=False, alias="E2E_KEEP_RESOURCES")
    # Zpods that reached a real terminal *failure* state (DEPLOY_FAILED,
    # DESTROY_FAILED) are left in place by default, even when keep_resources
    # is False - an operator debugging a failed deploy needs to actually
    # look at the broken VM/vCenter state, not just read the error message.
    # Successful (ACTIVE) zpods are still cleaned up normally. Set this to
    # false to fully auto-clean, including failures, like before.
    keep_failed_resources: bool = Field(default=True, alias="E2E_KEEP_FAILED_RESOURCES")

    prefect_ui_url: str = Field(default="", alias="E2E_PREFECT_UI_URL")
    prefect_api_url: str = Field(default="", alias="E2E_PREFECT_API_URL")

    deploy_timeout_seconds: int = Field(
        default=2400, alias="E2E_DEPLOY_TIMEOUT_SECONDS"
    )
    # The slow concurrency batch deploys vcd-prod/base8 replicas side by
    # side; vcd-prod alone takes ~55 min that way, past the default above.
    # Two hours: a large profile not deployed by then has a real problem.
    slow_deploy_timeout_seconds: int = Field(
        default=7200, alias="E2E_SLOW_DEPLOY_TIMEOUT_SECONDS"
    )
    component_download_timeout_seconds: int = Field(
        default=3600, alias="E2E_COMPONENT_DOWNLOAD_TIMEOUT_SECONDS"
    )
    poll_interval_seconds: int = Field(default=10, alias="E2E_POLL_INTERVAL_SECONDS")
    concurrency_max_workers: int = Field(
        default=15, alias="E2E_CONCURRENCY_MAX_WORKERS"
    )


class ConfigError(Exception):
    """Raised when required e2e configuration is missing or invalid."""


def load_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:  # pydantic ValidationError, mainly missing required fields
        raise ConfigError(
            "e2e config is incomplete. Copy .env.sample to .env and fill in the "
            f"required values (E2E_API_BASE_URL, E2E_SUPERADMIN_TOKEN, "
            f"E2E_ENDPOINT_NAME, E2E_DNS_RESOLVER).\nOriginal error: {e}"
        ) from e
