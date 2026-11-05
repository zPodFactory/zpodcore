"""SDK-direct client construction.

Mirrors `zpodcli.lib.zpod_client.ZpodClient` (subclassing the generated
`zpodsdk.zpod_client.ZpodClient` and passing the `access_token` header) but
sourced entirely from e2e config instead of a `.zclirc` factory file.
"""

from zpodsdk import zpod_client


class ZpodClient(zpod_client.ZpodClient):
    def __init__(self, base_url: str, token: str, raise_on_unexpected_status: bool = True):
        super().__init__(
            base_url=base_url,
            headers={"access_token": token},
            raise_on_unexpected_status=raise_on_unexpected_status,
        )


def build_client(base_url: str, token: str) -> ZpodClient:
    return ZpodClient(base_url=base_url, token=token)
