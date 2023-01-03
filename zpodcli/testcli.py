from rich import print
from zpod import AuthenticatedClient, Client
from zpod.api.users import get_users
from zpod.models import UserView
from zpod.types import Response

# Current way
zc = Client(base_url="http://localhost:8000")
zc.headers["access_token"] = "supertoken"


try:
    # or if you need more info (e.g. status_code)
    response: Response[UserView] = get_users.sync(client=zc)
    print(response)
except Exception as e:
    print(e)
