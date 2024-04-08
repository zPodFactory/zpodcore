import json
from functools import wraps

from zpodcli import __version__
from zpodcli.lib.factory_config import FactoryConfig
from zpodcli.lib.utils import exit_with_error
from zpodsdk import zpod_client
from zpodsdk.errors import UnexpectedStatus


class ZpodClient(zpod_client.ZpodClient):
    def __init__(
        self,
        base_url=None,
        token=None,
        raise_on_unexpected_status=True,
        **args,
    ):
        if not base_url and not token:
            fc = FactoryConfig()
            base_url = fc.factory["zpod_api_url"]
            token = fc.factory["zpod_api_token"]
        super().__init__(
            base_url=base_url,
            headers={
                "access_token": token,
                "version": __version__,
            },
            raise_on_unexpected_status=raise_on_unexpected_status,
            **args,
        )


def exit_if_status(status_code, content):
    content = content.decode() if isinstance(content, bytes) else content

    if 100 <= status_code < 200 or 300 <= status_code < 400:
        exit_with_error("Unable to handle response")
    elif 400 <= status_code < 500:
        try:
            content_json = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            exit_with_error(f"Unknown Error: {content} [{status_code}]")

        if status_code == 404:
            exit_with_error(content_json.get("detail", "Record not found."))
        elif status_code == 417:
            # CLI version doesn't match api version
            expected_version = content_json["detail"]["expected_version"]
            provided_version = content_json["detail"]["provided_version"]
            exit_with_error(
                f"zpodcli version {expected_version} is required. "
                f"Current zpodcli version is {provided_version}. "
                "Run the following command to upgrade your zpodcli to the proper version:\n"  # noqa: E501
                f"    pip install zpodcli=={expected_version}\n"
            )
        elif status_code == 422:
            messages = [
                rf"{error['msg']} \[{', '.join(error['loc'][1:])}]"
                for error in content_json["detail"]
            ]
            exit_with_error("\n  ".join(messages))
        else:
            exit_with_error(f"{content_json['detail']} [{status_code}]")
    elif 500 <= status_code < 600:
        exit_with_error(f"{content} [{status_code}]")


def unexpected_status_handler(func):
    @wraps(func)
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except UnexpectedStatus as e:
            exit_if_status(e.status_code, e.content)

    return inner_function
