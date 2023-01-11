from zpod import zpod_client

from zpodcli.lib.config import config


class ZpodClient(zpod_client.ZpodClient):
    def __init__(self, base_url=None, token=None):
        if not base_url and not token:
            cfg = config()
            base_url = cfg.get("zpod_api_url")
            token = cfg.get("zpod_api_token")
        super().__init__(base_url, token)
