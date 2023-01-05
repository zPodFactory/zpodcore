from rich import print
from zpod.api.users import get_users
from zpod.client import Client
from zpod.zpod_client import ZpodClient

# Raw way
zc = Client(base_url="http://localhost:8000")
zc.headers["access_token"] = "supertoken"
print(get_users.sync(client=zc))

# Wrapped way
zc2 = ZpodClient(
    base_url="http://localhost:8000",
    token="supertoken",
)
print(zc2.users_get_users.sync())
