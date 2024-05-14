from prefect import task

from zpodcommon import models as M
from zpodcommon.lib.zboxapi import HTTPStatusError, RequestError, ZboxApiClient
from zpodengine.lib import database
from zpodengine.lib.vcsadeployer import vcsa_extract_iso, vcsa_fix_permissions
from zpodengine.zpod_component_add.zpod_component_add_utils import (
    handle_zpod_component_add_failure,
)


@task
@handle_zpod_component_add_failure
def zpod_component_add_pre_scripts(
    *,
    zpod_component_id: int,
):
    with database.get_session_ctx() as session:
        zpod_component = session.get(M.ZpodComponent, zpod_component_id)

        c = zpod_component.component
        if c.component_name != 'zbox':
            zb = ZboxApiClient.by_zpod(zpod_component.zpod)
            try:
                response = zb.post(
                    url="/hosts",
                    json={
                        "ip": zpod_component.ip,
                        "fqdn": zpod_component.hostname,
                    },
                )
                response.raise_for_status()
            except (RequestError, HTTPStatusError):
                print(f"{zb.base_url} failure.  Skipping...")

        match c.component_name:
            case "vcsa":
                print("--- vcsa ---")

                # Extract component iso content
                vcsa_extract_iso(c)

                # Set execute permissions on required binaries
                vcsa_fix_permissions(c)
